from odoo import models, fields, api
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

class PlanMaestroProduccion(models.Model):
    _name = 'panelhex.plan.maestro.produccion'
    _description = 'Plan Maestro de Producción'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_start desc'

    name = fields.Char(string='Nombre', required=True, copy=False, tracking=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True, tracking=True)
    date_start = fields.Date(string='Fecha de Inicio', required=True, tracking=True)
    date_end = fields.Date(string='Fecha de Fin', required=True, tracking=True)
    estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('confirmado', 'Confirmado'),
        ('planificado', 'Planificado'),
        ('en_proceso', 'En Proceso'),
        ('terminado', 'Terminado'),
        ('cancelado', 'Cancelado')
    ], string='Estado', default='borrador', tracking=True)
    safety_stock = fields.Float(string='Stock de Seguridad', tracking=True)
    demand_forecast = fields.Float(string='Demanda Pronosticada', compute='_compute_demand_forecast', store=True)
    suggested_replenishment = fields.Float(string='Reabastecimiento Sugerido', compute='_compute_suggested_replenishment', store=True)
    forecasted_stock = fields.Float(string='Stock Previsto', compute='_compute_forecasted_stock', store=True)
    monthly_data = fields.One2many('panelhex.plan.maestro.produccion.mensual', 'plan_id', string='Datos Mensuales')
    notas = fields.Text(string='Notas')

    @api.depends('monthly_data.demand_forecast')
    def _compute_demand_forecast(self):
        for record in self:
            record.demand_forecast = sum(record.monthly_data.mapped('demand_forecast'))

    @api.depends('monthly_data.suggested_replenishment')
    def _compute_suggested_replenishment(self):
        for record in self:
            record.suggested_replenishment = sum(record.monthly_data.mapped('suggested_replenishment'))

    @api.depends('monthly_data.forecasted_stock')
    def _compute_forecasted_stock(self):
        for record in self:
            record.forecasted_stock = sum(record.monthly_data.mapped('forecasted_stock'))

    @api.constrains('date_start', 'date_end')
    def _check_dates(self):
        for record in self:
            if record.date_start and record.date_end and record.date_start > record.date_end:
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

    @api.model
    def create(self, vals):
        plan = super(PlanMaestroProduccion, self).create(vals)
        plan._create_monthly_data()
        return plan

    def write(self, vals):
        res = super(PlanMaestroProduccion, self).write(vals)
        if 'date_start' in vals or 'date_end' in vals or 'product_id' in vals or 'safety_stock' in vals:
            self._create_monthly_data()
        return res

    def _create_monthly_data(self):
        self.ensure_one()
        self.monthly_data.unlink()
        current_date = self.date_start
        while current_date <= self.date_end:
            next_month = current_date + relativedelta(months=1)
            month_end = next_month - relativedelta(days=1)
            if month_end > self.date_end:
                month_end = self.date_end

            self.env['panelhex.plan.maestro.produccion.mensual'].create({
                'plan_id': self.id,
                'date': current_date,
                'product_id': self.product_id.id,
            })

            current_date = next_month

    def action_generate_production_orders(self):
        self.ensure_one()
        if self.estado != 'confirmado':
            raise ValidationError("Solo se pueden generar órdenes de producción para planes confirmados.")

        for monthly_data in self.monthly_data:
            if monthly_data.suggested_replenishment > 0:
                existing_mo = self.env['mrp.production'].search([
                    ('product_id', '=', self.product_id.id),
                    ('date_planned_start', '=', monthly_data.date),
                    ('origin', '=', f"PMP-{self.name}-{monthly_data.date.strftime('%Y-%m')}")
                ])
                if not existing_mo:
                    self.env['mrp.production'].create({
                        'product_id': self.product_id.id,
                        'product_qty': monthly_data.suggested_replenishment,
                        'date_planned_start': monthly_data.date,
                        'origin': f"PMP-{self.name}-{monthly_data.date.strftime('%Y-%m')}",
                    })

        self.write({'estado': 'planificado'})

class PlanMaestroProduccionMensual(models.Model):
    _name = 'panelhex.plan.maestro.produccion.mensual'
    _description = 'Datos Mensuales del Plan Maestro de Producción'
    _order = 'date'

    plan_id = fields.Many2one('panelhex.plan.maestro.produccion', string='Plan Maestro', required=True, ondelete='cascade')
    date = fields.Date(string='Mes', required=True)
    product_id = fields.Many2one('product.product', string='Producto', required=True)
    demand_forecast = fields.Float(string='Demanda Pronosticada', compute='_compute_monthly_data', store=True)
    suggested_replenishment = fields.Float(string='Reabastecimiento Sugerido', compute='_compute_monthly_data', store=True)
    forecasted_stock = fields.Float(string='Stock Previsto', compute='_compute_monthly_data', store=True)

    @api.depends('plan_id', 'date', 'product_id')
    def _compute_monthly_data(self):
        for record in self:
            # Cálculo de la demanda pronosticada mensual
            start_date = record.date
            end_date = start_date + relativedelta(months=1) - relativedelta(days=1)
            forecasts = self.env['sale.forecast'].search([
                ('product_id', '=', record.product_id.id),
                ('date', '>=', start_date),
                ('date', '<=', end_date)
            ])
            record.demand_forecast = sum(forecasts.mapped('forecast_qty'))

            # Obtener el stock previsto del mes anterior
            previous_month_data = self.search([
                ('plan_id', '=', record.plan_id.id),
                ('date', '<', record.date)
            ], order='date desc', limit=1)
            previous_stock = previous_month_data.forecasted_stock if previous_month_data else record.product_id.qty_available

            safety_stock = record.plan_id.safety_stock
            record.suggested_replenishment = max(0, record.demand_forecast + safety_stock - previous_stock)

            # Cálculo del stock previsto (considerando la producción planificada)
            planned_production = self.env['mrp.production'].search([
                ('product_id', '=', record.product_id.id),
                ('date_planned_start', '>=', start_date),
                ('date_planned_start', '<', end_date),
                ('state', 'not in', ['cancel', 'done'])
            ]).mapped('product_qty')
            record.forecasted_stock = previous_stock + sum(planned_production) - record.demand_forecast