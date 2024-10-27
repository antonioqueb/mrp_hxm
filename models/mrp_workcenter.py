from odoo import models, fields

class MrpWorkcenter(models.Model):
    _inherit = 'mrp.workcenter'

<<<<<<< HEAD
    equipo_id = fields.Many2one('Hexamex.equipo', string='Equipo Hexamex')
=======
    equipo_id = fields.Many2one('panelhex.equipo', string='Equipo Hexamex')
>>>>>>> 15e4d56 (Up)
