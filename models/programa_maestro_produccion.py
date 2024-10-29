# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ProgramaMaestroProduccion(models.Model):
    _name = 'panelhex.programa.maestro.produccion'
    _description = 'Programa Maestro de Producción'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'fecha_inicio desc'

    name = fields.Char(string='Referencia', required=True, copy=False, readonly=True, default='Nuevo')
    fecha_inicio = fields.Date(string='Fecha de Inicio', required=True, tracking=True)
    fecha_fin = fields.Date(string='Fecha de Fin', required=True, tracking=True)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('en_proceso', 'En Proceso'),
        ('terminado', 'Terminado'),
        ('cancelado', 'Cancelado')
    ], string='Estado', default='borrador', tracking=True)
    linea_ids = fields.One2many('panelhex.programa.maestro.produccion.linea', 'programa_id', string='Líneas de Producción')
    notas = fields.Text(string='Notas')

    @api.model
    def create(self, vals):
        if vals.get('name', 'Nuevo') == 'Nuevo':
            vals['name'] = self.env['ir.sequence'].next_by_code('panelhex.programa.maestro.produccion') or 'Nuevo'
        return super(ProgramaMaestroProduccion, self).create(vals)

    @api.constrains('fecha_inicio', 'fecha_fin')
    def _check_fechas(self):
        for record in self:
            if record.fecha_inicio and record.fecha_fin and record.fecha_inicio > record.fecha_fin:
                raise ValidationError("La fecha de inicio no puede ser posterior a la fecha de fin.")

    def action_confirmar(self):
        self.write({'estado': 'confirmado'})

    def action_iniciar(self):
        self.write({'estado': 'en_proceso'})

    def action_terminar(self):
        self.write({'estado': 'terminado'})

    def action_cancelar(self):
        self.write({'estado': 'cancelado'})

    def action_borrador(self):
        self.write({'estado': 'borrador'})

class ProgramaMaestroProduccionLinea(models.Model):
    _name = 'panelhex.programa.maestro.produccion.linea'
    _description = 'Línea de Programa Maestro de Producción'

    programa_id = fields.Many2one('panelhex.programa.maestro.produccion', string='Programa Maestro', required=True, ondelete='cascade')
    producto_id = fields.Many2one('product.product', string='Producto', required=True)
    cantidad = fields.Float(string='Cantidad', required=True)
    fecha_planificada = fields.Date(string='Fecha Planificada', required=True)
    estado = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('en_proceso', 'En Proceso'),
        ('completado', 'Completado')
    ], string='Estado', default='pendiente')
    notas = fields.Text(string='Notas')