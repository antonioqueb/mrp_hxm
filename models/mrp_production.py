from odoo import models, fields, api

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    cambio_rapido = fields.Boolean(string='Cambio Rápido', help='Marcar si se realiza un cambio rápido')
    tiempo_cambio = fields.Float(string='Tiempo de Cambio (minutos)', help='Tiempo empleado en el cambio rápido')

    def action_register_cambio_rapido(self):
        self.ensure_one()
        return {
            'name': 'Registrar Cambio Rápido',
            'type': 'ir.actions.act_window',
            'res_model': 'Hexamex.cambio.rapido.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_production_id': self.id}
        }