from odoo import models, fields

<<<<<<< HEAD
class HexamexEquipo(models.Model):
    _name = 'Hexamex.equipo'
=======
class PanelhexEquipo(models.Model):
    _name = 'panelhex.equipo'
>>>>>>> 15e4d56 (Up)
    _description = 'Equipo Hexamex'

    name = fields.Char(string='Nombre del Equipo', required=True)
    descripcion = fields.Text(string='Descripción')
    workcenter_ids = fields.One2many('mrp.workcenter', 'equipo_id', string='Centros de Trabajo')