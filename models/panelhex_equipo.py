from odoo import models, fields

class HexamexEquipo(models.Model):
    _name = 'Hexamex.equipo'
    _description = 'Equipo Hexamex'

    name = fields.Char(string='Nombre del Equipo', required=True)
    descripcion = fields.Text(string='Descripción')
    workcenter_ids = fields.One2many('mrp.workcenter', 'equipo_id', string='Centros de Trabajo')