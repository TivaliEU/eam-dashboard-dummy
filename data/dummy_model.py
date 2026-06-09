from types import SimpleNamespace

# ---------------------------------------------------------------------------
# Nodes — 8 ArchiMate-Konzepte über Business- und Applikationsschicht
# ---------------------------------------------------------------------------
nodes = [
    # Business Layer
    SimpleNamespace(
        uid=1,
        stereotypename='business-role',
        displayname='Sachbearbeiter',
        uuid='a1b2c3d4-0001-0000-0000-000000000001',
    ),
    SimpleNamespace(
        uid=2,
        stereotypename='business-process',
        displayname='Kundendaten verwalten',
        uuid='a1b2c3d4-0002-0000-0000-000000000002',
    ),
    SimpleNamespace(
        uid=3,
        stereotypename='business-service',
        displayname='Auskunftsdienst',
        uuid='a1b2c3d4-0003-0000-0000-000000000003',
    ),
    # Application Layer
    SimpleNamespace(
        uid=4,
        stereotypename='application-component',
        displayname='CRM System',
        uuid='a1b2c3d4-0004-0000-0000-000000000004',
    ),
    SimpleNamespace(
        uid=5,
        stereotypename='application-component',
        displayname='DokSys Backend',
        uuid='a1b2c3d4-0005-0000-0000-000000000005',
    ),
    SimpleNamespace(
        uid=6,
        stereotypename='application-service',
        displayname='Dokumentenverwaltung',
        uuid='a1b2c3d4-0006-0000-0000-000000000006',
    ),
    SimpleNamespace(
        uid=7,
        stereotypename='application-interface',
        displayname='REST API Gateway',
        uuid='a1b2c3d4-0007-0000-0000-000000000007',
    ),
    SimpleNamespace(
        uid=8,
        stereotypename='data-object',
        displayname='Kundendaten',
        uuid='a1b2c3d4-0008-0000-0000-000000000008',
    ),
]

# ---------------------------------------------------------------------------
# Connections — gerichtete ArchiMate-Beziehungen (source → target)
# ---------------------------------------------------------------------------
connections = [
    # Sachbearbeiter ist dem Prozess zugewiesen
    SimpleNamespace(
        uid=101,
        sourcenode=['a1b2c3d4-0001-0000-0000-000000000001'],  # Sachbearbeiter
        targetnode=['a1b2c3d4-0002-0000-0000-000000000002'],  # Kundendaten verwalten
        stereotypename='assignment',
        displayname='assignment@Sachbearbeiter führt Kundendaten verwalten durch',
        uuid='c0000000-0101-0000-0000-000000000101',
    ),
    # Prozess realisiert den Business Service
    SimpleNamespace(
        uid=102,
        sourcenode=['a1b2c3d4-0002-0000-0000-000000000002'],  # Kundendaten verwalten
        targetnode=['a1b2c3d4-0003-0000-0000-000000000003'],  # Auskunftsdienst
        stereotypename='realization',
        displayname='realization@Prozess realisiert Auskunftsdienst',
        uuid='c0000000-0102-0000-0000-000000000102',
    ),
    # CRM System bedient den Business-Prozess
    SimpleNamespace(
        uid=103,
        sourcenode=['a1b2c3d4-0004-0000-0000-000000000004'],  # CRM System
        targetnode=['a1b2c3d4-0002-0000-0000-000000000002'],  # Kundendaten verwalten
        stereotypename='serving',
        displayname='serving@CRM System unterstützt Kundendaten verwalten',
        uuid='c0000000-0103-0000-0000-000000000103',
    ),
    # DokSys Backend realisiert den App Service
    SimpleNamespace(
        uid=104,
        sourcenode=['a1b2c3d4-0005-0000-0000-000000000005'],  # DokSys Backend
        targetnode=['a1b2c3d4-0006-0000-0000-000000000006'],  # Dokumentenverwaltung
        stereotypename='realization',
        displayname='realization@DokSys Backend realisiert Dokumentenverwaltung',
        uuid='c0000000-0104-0000-0000-000000000104',
    ),
    # REST API ist Teil des DokSys Backends (Komposition)
    SimpleNamespace(
        uid=105,
        sourcenode=['a1b2c3d4-0005-0000-0000-000000000005'],  # DokSys Backend
        targetnode=['a1b2c3d4-0007-0000-0000-000000000007'],  # REST API Gateway
        stereotypename='composition',
        displayname='composition@DokSys Backend enthält REST API Gateway',
        uuid='c0000000-0105-0000-0000-000000000105',
    ),
    # DokSys Backend liest/schreibt Kundendaten
    SimpleNamespace(
        uid=106,
        sourcenode=['a1b2c3d4-0005-0000-0000-000000000005'],  # DokSys Backend
        targetnode=['a1b2c3d4-0008-0000-0000-000000000008'],  # Kundendaten
        stereotypename='access',
        displayname='access@DokSys Backend greift auf Kundendaten zu',
        uuid='c0000000-0106-0000-0000-000000000106',
    ),
    # CRM System greift ebenfalls auf Kundendaten zu
    SimpleNamespace(
        uid=107,
        sourcenode=['a1b2c3d4-0004-0000-0000-000000000004'],  # CRM System
        targetnode=['a1b2c3d4-0008-0000-0000-000000000008'],  # Kundendaten
        stereotypename='access',
        displayname='access@CRM System liest und schreibt Kundendaten',
        uuid='c0000000-0107-0000-0000-000000000107',
    ),
    # Dokumentenverwaltungs-Service bedient den Prozess
    SimpleNamespace(
        uid=108,
        sourcenode=['a1b2c3d4-0006-0000-0000-000000000006'],  # Dokumentenverwaltung
        targetnode=['a1b2c3d4-0002-0000-0000-000000000002'],  # Kundendaten verwalten
        stereotypename='serving',
        displayname='serving@Dokumentenverwaltung unterstützt Kundendaten verwalten',
        uuid='c0000000-0108-0000-0000-000000000108',
    ),
    # CRM kommuniziert mit DokSys über REST API (association)
    SimpleNamespace(
        uid=109,
        sourcenode=['a1b2c3d4-0004-0000-0000-000000000004'],  # CRM System
        targetnode=['a1b2c3d4-0007-0000-0000-000000000007'],  # REST API Gateway
        stereotypename='association',
        displayname='association@CRM System kommuniziert über REST API Gateway',
        uuid='c0000000-0109-0000-0000-000000000109',
    ),
]
