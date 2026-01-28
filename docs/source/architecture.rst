Architecture
============

This document describes the architecture of the Conestack core packages and how
they work together to form a cohesive web application framework.

Overview
--------

The Conestack ecosystem consists of packages for different application domains.
Each package addresses a specific concern and can be used independently, though
they integrate when used together.

**Application Domains**

.. list-table::
   :header-rows: 1
   :widths: 20 80

   * - Package
     - Domain
   * - **plumber**
     - Behavior composition for classes
   * - **node**
     - Tree-based data structures
   * - **yafowil**
     - Form processing and validation
   * - **cone.app**
     - Web application framework

**Dependency Structure**

When used together, the packages have the following dependencies:

::

    ┌─────────────────────────────────────────────────────────────┐
    │                       cone.app                              │
    │            Web Framework, Tiles, Security                   │
    └─────────────────────────────────────────────────────────────┘
             │                                     │
             ▼                                     ▼
    ┌─────────────────────────┐     ┌─────────────────────────────┐
    │         node            │     │          yafowil            │
    │   Tree Structures       │◄────│   Form Processing           │
    └─────────────────────────┘     └─────────────────────────────┘
              │                                    │
              └──────────────┬─────────────────────┘
                             ▼
    ┌─────────────────────────────────────────────────────────────┐
    │                        plumber                              │
    │                 Behavior Composition                        │
    └─────────────────────────────────────────────────────────────┘


plumber - Behavior Composition
------------------------------

**plumber** is a library for composition-based class extension as an alternative
to mixins. It addresses requirements of behavior composition that are difficult
to achieve with traditional inheritance, such as explicit precedence control
and method pipelines, through a two-stage instruction system.

Package Structure
~~~~~~~~~~~~~~~~~

::

    src/plumber/
    ├── __init__.py      # Public API
    ├── plumber.py       # Metaclass and @plumbing decorator
    ├── behavior.py      # Behavior base class and metaclass
    ├── instructions.py  # All instructions (decorators)
    └── exceptions.py    # PlumbingCollision

Core Concepts
~~~~~~~~~~~~~

**Two-Stage Processing**

.. list-table::
   :header-rows: 1
   :widths: 15 25 30 30

   * - Stage
     - Timing
     - Instructions
     - Purpose
   * - Stage 1
     - Before class creation
     - ``default``, ``override``, ``finalize``
     - Attribute extension
   * - Stage 2
     - After class creation
     - ``plumb``, ``plumbifexists``
     - Method pipelines

**Precedence Hierarchy (Stage 1)**

::

    finalize > override > default

- ``default``: Weakest extension - only if attribute undefined
- ``override``: Medium strength - overrides base class, can be overridden by ``finalize``
- ``finalize``: Strongest extension - cannot be overridden

**Pipeline Creation (Stage 2)**

.. code-block:: python

    class MyBehavior(Behavior):
        @plumb
        def method(next_, self, arg):
            # next_ calls the next method in the pipeline
            result = next_(self, arg)
            return modified_result

Main Classes
~~~~~~~~~~~~

.. list-table::
   :widths: 30 70

   * - ``plumber`` (metaclass)
     - Controls class creation, applies instructions
   * - ``plumbing`` (decorator)
     - Decorator API for applying behaviors
   * - ``Behavior``
     - Base class for all behaviors
   * - ``Instruction``
     - Abstract base class for instructions
   * - ``default``, ``override``, ``finalize``
     - Stage 1 instructions
   * - ``plumb``, ``plumbifexists``
     - Stage 2 instructions

Usage Example
~~~~~~~~~~~~~

.. code-block:: python

    from plumber import plumbing, Behavior, default, override, plumb

    class LoggingBehavior(Behavior):
        @plumb
        def save(next_, self):
            print(f"Saving {self}")
            return next_(self)

    class ValidationBehavior(Behavior):
        valid = default(True)

        @plumb
        def save(next_, self):
            if not self.valid:
                raise ValueError("Invalid")
            return next_(self)

    @plumbing(LoggingBehavior, ValidationBehavior)
    class Model:
        def save(self):
            # Actual save logic
            pass

Design Patterns
~~~~~~~~~~~~~~~

- **Metaclass Pattern** - Central class creation control
- **Decorator Pattern** - ``@plumbing``, ``@default``, ``@override``, etc.
- **Chain of Responsibility** - Pipeline execution in ``plumb``
- **Composite Pattern** - Instructions combined via ``__add__``


node - Tree Data Structures
---------------------------

**node** is a library for tree-based data structures that implements the Zope
Location Protocol. It is built on plumber behaviors.

Package Structure
~~~~~~~~~~~~~~~~~

::

    src/node/
    ├── base.py              # Pre-built node classes
    ├── interfaces.py        # ~40 interface definitions
    ├── events.py            # Event classes and dispatcher
    ├── utils.py             # Helper functions
    ├── locking.py           # Locking utilities
    ├── serializer.py        # Tree serialization
    ├── behaviors/           # ~21 plumber behaviors
    │   ├── storage.py       # Dict/Odict/List storage
    │   ├── node.py          # Core node behavior
    │   ├── mapping.py       # Mapping protocol chain
    │   ├── sequence.py      # Sequence protocol chain
    │   ├── adopt.py         # Automatic child adoption
    │   ├── constraints.py   # Child validation
    │   ├── lifecycle.py     # Lifecycle events
    │   ├── reference.py     # UUID-based index
    │   ├── order.py         # Ordering operations
    │   ├── attributes.py    # Metadata storage
    │   ├── schema.py        # Typed fields
    │   ├── factories.py     # Dynamic child creation
    │   └── ...              # Additional behaviors
    └── schema/              # Schema validation
        ├── fields.py        # Field types
        └── serializer.py    # Field serializers

Core Concepts
~~~~~~~~~~~~~

**Zope Location Protocol**

.. code-block:: python

    node.__name__    # Name in parent
    node.__parent__  # Reference to parent
    node.path        # Path from root to here
    node.root        # Root node
    node.acquire(interface)  # Parent traversal

**Storage Types**

.. list-table::
   :header-rows: 1
   :widths: 25 25 50

   * - Storage Type
     - Classes
     - Interface
   * - Mapping (dict)
     - ``BaseNode``
     - ``IMappingNode``
   * - Mapping (odict)
     - ``OrderedNode``
     - ``IMappingNode`` + ``IOrdered``
   * - Sequence (list)
     - ``ListNode``
     - ``ISequenceNode``

**Behavior Layers (Pipeline from Top to Bottom)**

::

    Constraints     → Validation before child addition
    Adoption        → Sets __name__ and __parent__
    Lifecycle       → Fires events on changes
    References      → Maintains UUID index
    Attributes      → Separate metadata node
    Schema          → Type validation & serialization
    Factories       → Dynamic child creation
    Order           → Ordering operations
    Node            → Tree hierarchy & properties
    Mapping/Seq     → Dict/list-like API
    Storage         → Data backend (dict/odict/list)

Pre-built Node Classes
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from node.base import (
        AbstractNode,    # Minimal: only adoption + node hierarchy
        BaseNode,        # Unordered, dict-based
        OrderedNode,     # Ordered, odict-based
        ListNode,        # Sequence-based
        Node,            # With all standard behaviors (legacy)
        AttributedNode,  # Alias for Node
    )

Custom Node Creation
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from plumber import plumbing
    from node.behaviors import (
        MappingConstraints, MappingAdopt, DefaultInit,
        MappingNode, OdictStorage, MappingReference,
    )

    @plumbing(
        MappingConstraints,
        MappingAdopt,
        DefaultInit,
        MappingNode,
        MappingReference,
        OdictStorage,
    )
    class MyNode:
        child_constraints = (IMyInterface,)

Design Patterns
~~~~~~~~~~~~~~~

.. list-table::
   :widths: 30 70

   * - **Composite**
     - Tree structure of nodes
   * - **Plugin/Strategy**
     - Behaviors as interchangeable strategies
   * - **Chain of Responsibility**
     - Plumber pipeline
   * - **Decorator**
     - Behavior layers wrap each other
   * - **Observer**
     - Lifecycle events
   * - **Lazy Loading**
     - Factory behaviors
   * - **Index**
     - Reference system with UUID lookup


node.ext.* - Backend Extensions
-------------------------------

The ``node.ext.*`` packages provide adapters to expose various backend systems
as node trees:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Package
     - Description
   * - ``node.ext.directory``
     - File system directories as traversable tree structures
   * - ``node.ext.fs``
     - File system nodes with content access
   * - ``node.ext.ldap``
     - LDAP directories as node trees with full CRUD operations
   * - ``node.ext.ugm``
     - Abstract user/group management with pluggable backends
   * - ``node.ext.yaml``
     - YAML files as persistent node storage
   * - ``node.ext.zodb``
     - ZODB persistent object storage integration

These extensions allow applications to work with different storage backends
using the same node API.


yafowil - Form Library
----------------------

**yafowil** (Yet Another Form Widget Library) is a declarative, composition-based
form library. Instead of inheriting widget classes, widgets are composed via a
**Factory** from **Blueprints**.

Package Structure
~~~~~~~~~~~~~~~~~

::

    src/yafowil/
    ├── base.py           # Widget, RuntimeData, Factory, ExtractionError
    ├── controller.py     # Form controller for submissions
    ├── datatypes.py      # Data type conversion
    ├── persistence.py    # Persistence writers
    ├── utils.py          # Tag class, vocabularies, CSS helpers
    ├── loader.py         # Plugin system via entry points
    ├── common.py         # Generic extractors/renderers
    ├── compound.py       # Form, Fieldset, Div
    ├── field.py          # Label, Help, Error wrapper
    ├── text.py           # Text input blueprint
    ├── select.py         # Select/Dropdown blueprints
    ├── checkbox.py       # Checkbox blueprint
    ├── textarea.py       # Textarea blueprint
    ├── button.py         # Submit/Button blueprints
    ├── file.py           # File upload blueprint
    └── ...               # Additional blueprints

Core Concepts
~~~~~~~~~~~~~

**Blueprint System**

Blueprints are registered components with extractors, renderers, and preprocessors:

.. code-block:: python

    factory.register(
        'text',
        extractors=[generic_extractor, generic_required_extractor, ...],
        edit_renderers=[text_edit_renderer],
        display_renderers=[generic_display_renderer]
    )

**Blueprint Composition (Chain Syntax)**

.. code-block:: python

    # Single blueprint
    factory('text', name='field')

    # Multiple blueprints combined
    factory('error:label:text', name='field')  # Error → Label → Text
    factory('field:label:text', name='field')  # Field-Wrapper → Label → Text

**Dual Pipeline Architecture**

.. list-table::
   :header-rows: 1
   :widths: 20 20 60

   * - Pipeline
     - Direction
     - Purpose
   * - **Extraction**
     - Request → Data
     - Extract values, validate
   * - **Rendering**
     - Data → HTML
     - Generate HTML

::

    Extraction:  Request → [Extractor₁ → Extractor₂ → ... → Extractorₙ] → Validated Data
                                  ↓ ExtractionError stops at abort=True

    Rendering:   Data → [Renderer₁ → Renderer₂ → ... → Rendererₙ] → HTML
                             ↓ Each renderer wraps previous output

**Node Integration**

Widget and RuntimeData use node behaviors:

.. code-block:: python

    @plumbing(
        Attributes,
        MappingConstraints,
        MappingAdopt,
        MappingOrder,
        MappingNode,
        OdictStorage
    )
    class Widget(object):
        ...

Main Classes
~~~~~~~~~~~~

.. list-table::
   :widths: 25 75

   * - ``Widget``
     - Configured widget node with chains
   * - ``RuntimeData``
     - Processing state during extract/render
   * - ``Factory``
     - Registry and builder for widgets
   * - ``ExtractionError``
     - Validation error with abort flag
   * - ``Controller``
     - High-level form handling
   * - ``Tag``
     - HTML generation without templates

Usage Example
~~~~~~~~~~~~~

.. code-block:: python

    from yafowil.base import factory, Controller
    from yafowil.persistence import attribute_writer

    # Create form
    form = factory('form', name='contact', props={
        'form.action': '/submit',
        'form.method': 'post'
    })

    # Add child widgets
    form['name'] = factory('error:label:text', props={
        'label.label': 'Name',
        'required': True
    })

    form['email'] = factory('error:label:email', props={
        'label.label': 'Email',
        'required': True
    })

    def handle_submit(widget, data):
        print("Submitted:", data.extracted)

    form['submit'] = factory('submit', props={
        'submit.action': True,
        'submit.handler': handle_submit
    })

    # Extraction and rendering
    request = {'contact.name': 'John', 'contact.email': 'john@example.com'}
    data = form.extract(request)

    if data.has_errors:
        html = form(data=data)  # Render with errors
    else:
        data.write(model, writer=attribute_writer)

Extension Mechanisms
~~~~~~~~~~~~~~~~~~~~

**Custom Blueprint**

.. code-block:: python

    @managedprops('my_prop')
    def my_extractor(widget, data):
        if not valid(data.extracted):
            raise ExtractionError('Invalid')
        return data.extracted

    factory.register('mycustom', extractors=[my_extractor], ...)

**Asterisk Syntax (Inline Custom)**

.. code-block:: python

    widget = factory('label:*validate:text', name='field', custom={
        'validate': ([my_extractor], [], [], [], [])
    })

**Macros**

.. code-block:: python

    factory.register_macro('required_text', 'error:label:text', {
        'required': True
    })
    widget = factory('#required_text', name='field')

**Plugin System (Entry Points)**

.. code-block:: toml

    [project.entry-points."yafowil.plugin"]
    register = "mypackage:register"

Design Patterns
~~~~~~~~~~~~~~~

.. list-table::
   :widths: 30 70

   * - **Factory**
     - Central widget creation
   * - **Chain of Responsibility**
     - Extractor/renderer pipelines
   * - **Composite**
     - Widget tree via node
   * - **Registry**
     - Blueprint registry in Factory
   * - **Strategy**
     - Interchangeable persistence writers
   * - **Decorator**
     - ``@managedprops`` for property documentation


yafowil.widget.* - Widget Extensions
------------------------------------

The ``yafowil.widget.*`` packages provide specialized form widgets:

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Package
     - Description
   * - ``yafowil.widget.ace``
     - Ace code editor integration
   * - ``yafowil.widget.array``
     - Dynamic array/list fields
   * - ``yafowil.widget.autocomplete``
     - Autocomplete text input
   * - ``yafowil.widget.chosen``
     - Chosen.js select enhancement
   * - ``yafowil.widget.color``
     - Color picker widget
   * - ``yafowil.widget.cron``
     - Cron expression editor
   * - ``yafowil.widget.datetime``
     - Date and time pickers
   * - ``yafowil.widget.dict``
     - Key-value dictionary fields
   * - ``yafowil.widget.dynatree``
     - Tree selection widget
   * - ``yafowil.widget.image``
     - Image upload and preview
   * - ``yafowil.widget.location``
     - Location/address picker with maps
   * - ``yafowil.widget.multiselect``
     - Multi-select list widget
   * - ``yafowil.widget.richtext``
     - Rich text editor integration
   * - ``yafowil.widget.select2``
     - Select2.js integration
   * - ``yafowil.widget.slider``
     - Range slider widget
   * - ``yafowil.widget.tiptap``
     - Tiptap rich text editor
   * - ``yafowil.widget.wysihtml5``
     - WYSIHTML5 editor integration

Each widget package registers its blueprints via the yafowil plugin system,
making them automatically available after installation.


cone.app - Web Application Framework
------------------------------------

**cone.app** is the main web application framework of the Conestack ecosystem.
It builds on Pyramid and integrates the other packages, providing tile-based
UI composition, ACL-based security, and a plugin architecture.

Package Structure
~~~~~~~~~~~~~~~~~

::

    src/cone/app/
    ├── __init__.py          # WSGI app factory, configuration, bootstrapping
    ├── model.py             # Core node models and behaviors
    ├── security.py          # Authentication, authorization, ACLs
    ├── interfaces.py        # Zope interface definitions
    ├── workflow.py          # Workflow state management
    ├── ugm.py               # User/group management backend
    ├── utils.py             # Helper functions
    ├── browser/             # Views, tiles, UI components
    │   ├── __init__.py      # Main view, layout helpers
    │   ├── actions.py       # Action system (toolbars, buttons)
    │   ├── layout.py        # Layout tiles (navbar, menu, sidebar)
    │   ├── contents.py      # Content listing table
    │   ├── authoring.py     # Add/Edit forms
    │   ├── ajax.py          # AJAX rendering and continuations
    │   ├── sharing.py       # ACL editor
    │   ├── form.py          # Yafowil integration
    │   └── ...              # Additional browser modules
    └── testing/             # Test utilities

Core Concepts
~~~~~~~~~~~~~

**Node-based Content Model**

All content is represented as nodes in a tree structure (like a file system):

.. code-block:: python

    root = get_root()
    root['documents']['report'] = DocumentNode()

    # Navigation via traversal
    node = root['documents']['report']
    node.path      # ['', 'documents', 'report']
    node.parent    # documents node
    node.root      # root node

**Pyramid Integration**

.. code-block:: python

    def main(global_config, **settings):
        """WSGI Application Factory."""
        config = Configurator(root_factory=get_root, settings=settings)

        # Authentication (cookie-based)
        config.set_authentication_policy(auth_tkt_factory(...))

        # Authorization (ACL-based)
        config.set_authorization_policy(acl_factory())

        # Plugin loading
        for plugin in settings.get('cone.plugins', '').split():
            config.load_zcml(f'{plugin}:configure.zcml')

        # Execute main hooks
        for hook in main_hooks:
            hook(config, global_config, settings)

        return config.make_wsgi_app()

**Tile-based UI (cone.tile)**

Tiles are composable view components:

.. code-block:: python

    @tile(name='content', path='templates/content.pt', permission='view')
    class ContentTile(Tile):
        @property
        def items(self):
            return self.model.values()

**Main Tiles**

.. list-table::
   :widths: 20 80

   * - ``layout``
     - Main layout container
   * - ``mainmenu``
     - Navigation menu from node hierarchy
   * - ``pathbar``
     - Breadcrumb navigation
   * - ``content``
     - Main content area
   * - ``listing``
     - Child listing with sorting/batching
   * - ``sharing``
     - ACL editor table

**Security Model**

ACL-based authorization:

.. code-block:: python

    DEFAULT_ACL = [
        (Allow, 'system.Authenticated', authenticated_permissions),
        (Allow, 'role:viewer', ['view', 'list']),
        (Allow, 'role:editor', ['view', 'list', 'add', 'edit']),
        (Allow, 'role:admin', ['view', 'list', 'add', 'edit', 'delete', 'manage']),
        (Allow, 'role:manager', ALL_PERMISSIONS),
        (Deny, Everyone, ALL_PERMISSIONS),
    ]

Authentication sources (in order):

1. Admin user (via settings)
2. Custom authenticator
3. UGM backend (Users/Groups Management)

**Action System**

.. code-block:: python

    @tile(name='contexttoolbar', permission='view')
    class ContextToolbar(Toolbar):
        def __call__(self, model, request):
            self.add(ActionView())
            self.add(ActionEdit())
            if model.properties.action_delete:
                self.add(ActionDelete())
            return super().__call__(model, request)

Main Classes
~~~~~~~~~~~~

**Model Classes (model.py)**

.. list-table::
   :widths: 25 75

   * - ``AppNode``
     - Behavior for IApplicationNode interface
   * - ``BaseNode``
     - Node with storage, lifecycle, and common behaviors
   * - ``FactoryNode``
     - Node with dynamic children via factories
   * - ``AppRoot``
     - Root node of the application
   * - ``AppSettings``
     - Container for plugin settings
   * - ``AdapterNode``
     - Adapts external models into node hierarchy
   * - ``Properties``
     - Dynamic node properties container
   * - ``Metadata``
     - Display metadata (title, description, icon)
   * - ``LayoutConfig``
     - Configuration for page layout

**Security Classes (security.py)**

.. list-table::
   :widths: 25 75

   * - ``OwnerSupport``
     - Behavior for owner tracking
   * - ``PrincipalACL``
     - Behavior for principal-specific ACLs
   * - ``AdapterACL``
     - ACL derivation from registered adapters
   * - ``ACLRegistry``
     - Registry for ACL lookup

Plugin Development
~~~~~~~~~~~~~~~~~~

.. code-block:: python

    # myapp/__init__.py
    from cone.app import main_hook, register_entry
    from cone.app.model import BaseNode

    class MyContentNode(BaseNode):
        pass

    @main_hook
    def my_plugin_hook(config, global_config, settings):
        # Register entry node
        register_entry('mycontent', MyContentNode)

        # Scan views
        config.scan('myapp.browser')

        # Static resources
        config.add_static_view('myapp-static', 'myapp:static')

**INI Configuration**

.. code-block:: ini

    [app:main]
    use = egg:cone.app

    cone.plugins = myapp
    cone.root.title = My Application
    cone.admin_user = admin
    cone.admin_password = secret

    ugm.backend = file
    ugm.users_file = %(here)s/var/users.txt

Extension Mechanisms
~~~~~~~~~~~~~~~~~~~~

**Entry/Config Registration**

.. code-block:: python

    # Register top-level node
    register_entry('documents', DocumentsNode)

    # Register settings node
    register_config('myapp_settings', MySettingsNode)

**node_info Decorator**

.. code-block:: python

    @node_info(
        name='document',
        title='Document',
        description='A document node',
        addables=['document', 'folder'],
        icon='glyphicon glyphicon-file'
    )
    class DocumentNode(BaseNode):
        pass

**layout_config Decorator**

.. code-block:: python

    @layout_config(DocumentNode)
    class DocumentLayout(LayoutConfig):
        mainmenu = True
        sidebar_left = ['navtree']
        sidebar_left_grid_width = 3
        content_grid_width = 9

**Main Hooks**

.. code-block:: python

    @main_hook
    def setup_resources(config, global_config, settings):
        # Executed at app startup
        cone.app.cfg.css.public.append('myapp-static/styles.css')
        cone.app.cfg.js.public.append('myapp-static/app.js')

Design Patterns
~~~~~~~~~~~~~~~

.. list-table::
   :widths: 30 70

   * - **Composite**
     - Node tree for content
   * - **Factory**
     - Node factories, app factory
   * - **Registry**
     - ACL registry, entry registry
   * - **Adapter**
     - Zope adapters for traversal, ACLs
   * - **Template Method**
     - Tile rendering with overridable methods
   * - **Strategy**
     - Interchangeable UGM backends
   * - **Observer**
     - Lifecycle events
   * - **Command**
     - Action system


cone.* - Feature Packages
-------------------------

Additional cone packages provide specialized features:

.. list-table::
   :header-rows: 1
   :widths: 25 75

   * - Package
     - Description
   * - ``cone.tile``
     - Tile-based UI composition system
   * - ``cone.ugm``
     - User/group management UI with LDAP/SQL backends
   * - ``cone.ldap``
     - LDAP backend integration for cone.app
   * - ``cone.sql``
     - SQL database integration with SQLAlchemy
   * - ``cone.zodb``
     - ZODB backend integration for persistent nodes
   * - ``cone.calendar``
     - Calendar functionality with event management
   * - ``cone.charts``
     - Chart visualizations with various chart types
   * - ``cone.fileupload``
     - File upload handling with progress tracking
   * - ``cone.firebase``
     - Firebase integration for push notifications
   * - ``cone.maps``
     - Map widgets with location data
   * - ``cone.tokens``
     - Token management for secure operations


Architecture Summary
--------------------

Architecture Principles
~~~~~~~~~~~~~~~~~~~~~~~

The packages share common architecture principles:

1. **Composition over Inheritance** - Behaviors/blueprints instead of class hierarchies
2. **Explicit over Implicit** - Explicit instructions for class composition
3. **Pipeline-based Processing** - Chain of responsibility for extensibility
4. **Interface Segregation** - Small, focused interfaces/behaviors
5. **Fail Fast** - Errors at definition/creation time instead of runtime
6. **Node Traversal** - Tree structures as common data model

Dependency Graph
~~~~~~~~~~~~~~~~

::

    cone.app
       ├── cone.tile (tile rendering)
       ├── yafowil (forms)
       │     └── webresource (resource management)
       ├── node (content model + widget tree structure)
       │     └── plumber (behavior composition)
       ├── Pyramid (web framework)
       └── zope.interface (component architecture)

**Direct node usage in cone.app:**

- ``AppRoot``, ``BaseNode``, ``FactoryNode`` etc. are based on node behaviors
- Traversal-based URL routing via the node hierarchy
- Content model is a node tree with ``__name__``/``__parent__``
- yafowil uses node for its widget tree structure

Layer Architecture
~~~~~~~~~~~~~~~~~~

::

    ┌────────────────────────────────────────────────────────────────────┐
    │                        Application Layer                           │
    │  cone.app plugins, custom nodes, custom tiles, business logic      │
    ├────────────────────────────────────────────────────────────────────┤
    │                        Framework Layer                             │
    │  cone.app (web app), cone.tile (UI), yafowil (forms)               │
    ├────────────────────────────────────────────────────────────────────┤
    │                      Data Structure Layer                          │
    │  node (trees), node.ext.* (backend adapters)                       │
    ├────────────────────────────────────────────────────────────────────┤
    │                        Meta Layer                                  │
    │  plumber (behavior composition), zope.interface (contracts)        │
    ├────────────────────────────────────────────────────────────────────┤
    │                      Infrastructure Layer                          │
    │  Pyramid, WSGI, Python                                             │
    └────────────────────────────────────────────────────────────────────┘

When to Use Which Package
~~~~~~~~~~~~~~~~~~~~~~~~~

.. list-table::
   :header-rows: 1
   :widths: 50 50

   * - Use Case
     - Package
   * - Web application with UI, security, and plugin system
     - cone.app
   * - Compose classes with configurable behaviors
     - plumber
   * - Model hierarchical data structures (trees)
     - node
   * - Build web forms
     - yafowil
   * - Expose backend data as tree (LDAP, FS, DB)
     - node.ext.*
   * - Bootstrap-styled forms
     - yafowil.bootstrap
   * - User/group management
     - cone.ugm
   * - SQL backend for cone.app
     - cone.sql
   * - ZODB backend for cone.app
     - cone.zodb

Standalone Usage
~~~~~~~~~~~~~~~~

The packages are modular and can be used independently:

- **plumber** - Standalone for behavior composition in any project
- **node** - Standalone for tree structures without web context
- **yafowil** - Standalone for forms in any web framework
- **cone.tile** - Standalone for tile-based rendering in Pyramid apps
