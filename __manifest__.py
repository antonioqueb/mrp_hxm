{
    'name': 'Hexamex MRP Extension',
    'version': '1.0',
    'category': 'Manufacturing',
    'summary': 'Extensión del módulo MRP para Hexamex',
    'description': """
        Este módulo extiende la funcionalidad del módulo MRP de Odoo para adaptarse a las necesidades específicas de Hexamex.
    """,
    'author': 'ALPHAQUEB CONSULTING SAS',
    'website': 'https://alphaqueb.com',
    'depends': ['mrp'],
    'data': [
        'security/Hexamex_security.xml',
        'security/ir.model.access.csv',
        'views/mrp_workorder_views.xml',
        'views/mrp_production_views.xml',
        'views/Hexamex_equipo_views.xml',
        'wizards/Hexamex_cambio_rapido_wizard_views.xml',
        'report/Hexamex_reports.xml',
        'report/Hexamex_report_templates.xml',
        'data/Hexamex_data.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}