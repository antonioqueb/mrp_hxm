{
    'name': 'PanelHex MRP Extension',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Extensión del módulo MRP para PanelHex',
    'description': """
        Este módulo extiende la funcionalidad del módulo MRP de Odoo para adaptarse a las necesidades específicas de PanelHex.
    """,
    'author': 'ALPHAQUEB CONSULTING SAS',
    'website': 'https://alphaqueb.com',
    'depends': ['base','mrp','sale',],
    'data': [
        'security/panelhex_security.xml',
        'security/ir.model.access.csv',
        'views/mrp_workorder_views.xml',
        'views/mrp_production_views.xml',
        'views/panelhex_equipo_views.xml',
        'views/programa_maestro_produccion_views.xml',
        'views/panelhex_workcenter_field_config_views.xml',
        'wizards/panelhex_cambio_rapido_wizard_views.xml',
        'report/panelhex_reports.xml',
        'report/panelhex_report_templates.xml',
        'data/panelhex_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}