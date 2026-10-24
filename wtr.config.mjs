// Runs the JavaScript tests of all packages in `sources/` which provide a web
// test runner config. Each package becomes a test group named after the
// package, run a single one with `--group <package>`.
import {existsSync, readdirSync} from 'node:fs';
import {registerHooks} from 'node:module';
import {resolve} from 'node:path';
import {pathToFileURL} from 'node:url';
import {defaultReporter} from '@web/test-runner';
import {playwrightLauncher} from '@web/test-runner-playwright';

const PACKAGE_CONFIGS = ['js/wtr.config.mjs', 'wtr.config.mjs'];

// Package configs and tests are written for a dev server rooted at the
// package directory, this server is rooted at the repository.
const PACKAGE_ORIGIN = 'http://package';

// URL parameter passing the package under test to all modules a test imports.
const PACKAGE_PARAM = 'wtr-package';

function findPackageConfigs() {
    return readdirSync('sources').sort().flatMap(name => {
        const path = PACKAGE_CONFIGS
            .map(config => `sources/${name}/${config}`)
            .find(existsSync);
        return path ? [{name, url: pathToFileURL(resolve(path)).href}] : [];
    });
}

/**
 * Import the package configs.
 *
 * Package configs import web test runner packages from their own
 * node_modules. Resolving these from the repository root instead avoids
 * loading them once per package, which costs seconds and >1GB of memory.
 *
 * @param {Array<{name: string, url: string}>} configs - Package names and
 * config URLs.
 * @returns {Promise<Array<{name: string, files: string[], importMap: Object}>>}
 * Package names, test file patterns and import maps.
 */
async function loadPackages(configs) {
    const urls = new Set(configs.map(config => config.url));
    const hooks = registerHooks({
        resolve(specifier, context, nextResolve) {
            const bare = !/^\.{0,2}\//.test(specifier);
            if (bare && urls.has(context.parentURL)) {
                context = {...context, parentURL: import.meta.url};
            }
            return nextResolve(specifier, context);
        },
    });
    try {
        return await Promise.all(configs.map(async ({name, url}) => {
            const {default: config, importMap} = await import(url);
            if (!importMap) {
                throw new Error(`${url} must export its importMap`);
            }
            return {name, files: config.files, importMap};
        }));
    } finally {
        hooks.deregister();
    }
}

function toRootUrl(name, target) {
    const url = new URL(target, `${PACKAGE_ORIGIN}/`);
    if (url.origin !== PACKAGE_ORIGIN) {
        return target;
    }
    // Nested `sources/` checkouts of a package are siblings in the repository.
    if (url.pathname.startsWith('/sources/')) {
        return url.pathname;
    }
    return `/sources/${name}${url.pathname}`;
}

function toRootImports({name, importMap}) {
    const specifiers = Object.keys(importMap.imports);
    if (importMap.scopes || specifiers.some(s => s.endsWith('/'))) {
        throw new Error(
            `Import map of ${name}: only exact "imports" are supported`
        );
    }
    return Object.fromEntries(specifiers.map(specifier => [
        specifier,
        toRootUrl(name, importMap.imports[specifier])
    ]));
}

function withPackageParam(source, name) {
    const separator = source.includes('?') ? '&' : '?';
    return `${source}${separator}${PACKAGE_PARAM}=${encodeURIComponent(name)}`;
}

/**
 * Serve the tests of each package as if the dev server was rooted at the
 * package directory.
 *
 * All test pages are served from `/`, so the browser cannot scope import
 * maps or relative URLs per package. Instead:
 *
 * - Like `@web/dev-server-import-maps` does with import map ids, the package
 *   name is passed as URL parameter from the test file to every module it
 *   imports, and bare imports resolve with the import map of that package.
 *   Modules shared between packages, e.g. treibstoff, thus resolve their
 *   imports with the import map of the package under test.
 * - Files a test page requests relative to the document, e.g. stylesheets,
 *   are redirected to the package of the test if they exist there but not in
 *   the repository root.
 *
 * @param {Array<{name: string, importMap: Object}>} packages - Package names
 * and import maps.
 * @returns {{plugin: Object, middleware: Function}} Dev server plugin and
 * middleware.
 */
function packageScope(packages) {
    const imports = new Map(packages.map(p => [p.name, toRootImports(p)]));
    // test page path and query -> package name
    const testPages = new Map();
    const plugin = {
        name: 'package-scope',
        resolveImport({source, context}) {
            const name = context.URL.searchParams.get(PACKAGE_PARAM);
            return imports.get(name)?.[source];
        },
        transformImport({source, context}) {
            if (!context.response.is('html')) {
                const name = context.URL.searchParams.get(PACKAGE_PARAM);
                return name ? withPackageParam(source, name) : undefined;
            }
            // On a test page, the import to transform is the test file.
            const name = source.match(/^\/sources\/([^/]+)\//)?.[1];
            if (!name) {
                return undefined;
            }
            testPages.set(context.URL.pathname + context.URL.search, name);
            return withPackageParam(source, name);
        },
    };
    function middleware(context, next) {
        const referer = context.get('referer');
        const page = referer ? new URL(referer) : null;
        const name = page && testPages.get(page.pathname + page.search);
        const path = decodeURIComponent(context.path);
        if (name && !existsSync(`.${path}`) && existsSync(`sources/${name}${path}`)) {
            context.redirect(`/sources/${name}${context.url}`);
            return undefined;
        }
        return next();
    }
    return {plugin, middleware};
}

function countTests(results, counts) {
    for (const test of results?.tests ?? []) {
        const status = test.skipped ? 'skipped' : test.passed ? 'passed' : 'failed';
        counts[status] += 1;
    }
    for (const suite of results?.suites ?? []) {
        countTests(suite, counts);
    }
}

function formatCounts(name, counts) {
    const parts = ['passed', 'failed', 'skipped']
        .filter(status => status === 'passed' || counts[status])
        .map(status => `${counts[status]} ${status}`);
    if (counts.failedFiles) {
        parts.push(`${counts.failedFiles} failed test file(s)`);
    }
    const sign = counts.failedFiles ? '✗' : '✓';
    return `${sign} ${name.padEnd(30)} ${parts.join(', ')}`;
}

/**
 * Report test results per package once all tests have run.
 *
 * @returns {Object} Test runner reporter.
 */
function packageSummaryReporter() {
    return {
        onTestRunFinished({sessions}) {
            const packages = new Map();
            for (const session of sessions) {
                const name = session.group.name;
                if (!packages.has(name)) {
                    packages.set(name, {passed: 0, failed: 0, skipped: 0, failedFiles: 0});
                }
                const counts = packages.get(name);
                countTests(session.testResults, counts);
                counts.failedFiles += session.passed ? 0 : 1;
            }
            const lines = [...packages].map(([name, counts]) => formatCounts(name, counts));
            console.log(`\nTest results per package:\n${lines.join('\n')}\n`);
        },
    };
}

const packages = await loadPackages(findPackageConfigs());
const scope = packageScope(packages);

export default {
    nodeResolve: true,
    browsers: [
        playwrightLauncher({product: 'chromium'}),
    ],
    testFramework: {
        path: './node_modules/web-test-runner-qunit/dist/autorun.js',
        config: {
            noglobals: false
        }
    },
    groups: packages.map(({name, files}) => ({
        name,
        files: files.map(pattern => `sources/${name}/${pattern}`),
    })),
    coverageConfig: {
        include: ['sources/*/js/src/**/*.js', 'sources/treibstoff/src/**/*.js'],
        exclude: ['**/node_modules/**', 'sources/*/sources/**']
    },
    reporters: [defaultReporter(), packageSummaryReporter()],
    middleware: [scope.middleware],
    plugins: [scope.plugin],
}
