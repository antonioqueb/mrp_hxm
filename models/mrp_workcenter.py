from odoo import models, fields

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

    equipo_id = fields.Many2one('Hexamex.equipo', string='Equipo Hexamex')