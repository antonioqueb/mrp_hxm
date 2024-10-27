from odoo import models, fields, api

class PanelhexCambioRapidoWizard(models.TransientModel):
    _name = 'panelhex.cambio.rapido.wizard'
    _description = 'Wizard para registrar cambio rápido'

    production_id = fields.Many2one('mrp.production', string='Orden de Producción', required=True)
    tiempo_cambio = fields.Float(string='Tiempo de Cambio (minutos)', required=True)
    notas = fields.Text(string='Notas')

    def action_register_cambio_rapido(self):
        self.ensure_one()
        self.production_id.write({
            'cambio_rapido': True,
            'tiempo_cambio': self.tiempo_cambio,
        })
        return {'type': 'ir.actions.act_window_close'}