from odoo import models, fields, api

class MrpWorkorder(models.Model):
    _inherit = 'mrp.workorder'

    Hexamex_data_ids = fields.One2many('Hexamex.workorder.data', 'workorder_id', string='Datos Hexamex')

    @api.model
    def create(self, vals):
        res = super(MrpWorkorder, self).create(vals)
        if res.workcenter_id:
            self.create_default_workorder_data(res)
        return res

    def create_default_workorder_data(self, workorder):
        WorkorderData = self.env['Hexamex.workorder.data']
        workcenter_code = workorder.workcenter_id.code
        if workcenter_code == 'OCT':
            default_fields = [
                ('entrada_rollo_lote', 'char'),
                ('entrada_rollo_proveedor', 'many2one'),
                ('entrada_rollo_peso', 'float'),
                ('entrada_rollo_gramaje', 'float'),
                ('entrada_rollo_medidas', 'char'),
            ]
        elif workcenter_code == 'COR':
            default_fields = [
                ('entrada_lote_bloque', 'char'),
                ('salida_num_cortes', 'integer'),
            ]
        # Añadir más condiciones para otros tipos de centros de trabajo
        
        for field, field_type in default_fields:
            WorkorderData.create({
                'workorder_id': workorder.id,
                'name': field,
                'field_type': field_type,
            })