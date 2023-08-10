# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models
from odoo.exceptions import UserError


class OdooServerAction(models.Model):
    _name = 'server.action.remote'
    _description = 'Server Action'

    name = fields.Char('Action Name', required=True)
    host = fields.Char('Server URL', required=True)
    port = fields.Char('Port Protocol', required=True)
    username = fields.Char('Username', required=True)
    connection_type = fields.Selection([
        ('pass', 'Password'),
        ('key', 'SSH Key')
    ], string='Connection Type', default='pass')
    password = fields.Char('Password')
    path_key = fields.Char('Path Key')
    description = fields.Text('Description')
    timeout = fields.Integer('Timeout', default=30)

    command_start = fields.Char('Start Command', required=True)
    command_stop = fields.Char('Stop Command', required=True)
    command_restart = fields.Char('Restart Command', required=True)
    command_git_pull = fields.Char('Git Pull')
    command_backup_sql = fields.Char('Backup SQL')
    command_backup_data = fields.Char('Backup Data')

    history_ids = fields.One2many('server.action.remote.history', 'server_id')
    auto_delete_history_rotation = fields.Integer(string='Clean History Rotation', default=30, help="Histories will be deleted automaticlly if the number exceeds")

    def get_server_object(self):
        import paramiko

        try:
            client = paramiko.SSHClient()
            client.load_system_host_keys()

            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            if self.connection_type == 'key':
                key = paramiko.RSAKey.from_private_key_file(self.path_key)
                client.connect(hostname=self.host, port=self.port, username=self.username, pkey=key, timeout=self.timeout)
            else:
                client.connect(hostname=self.host, port=self.port, username=self.username, password=self.password, timeout=self.timeout)
            transport = client.get_transport()
            channel = transport.open_session()
            return {'status': 'success', 'object': channel}

        except Exception as e:
            return {'status': 'failed', 'exception': str(e)}

    def test_server_connection(self, raise_success=True, raise_failed=True):
        self.ensure_one()

        connection_data = self.get_server_object()

        if raise_success and connection_data['status'] == 'success':
            raise UserError("Successful connection !!\t")

        if raise_failed and connection_data['status'] == 'failed':
            raise UserError("Failed !!\nReason:\t" + str(connection_data['exception']))

    def action_start_server(self):
        self.ensure_one()
        self.test_server_connection(raise_success=False)
        connection_data = self.get_server_object()
        channel = connection_data['object']
        channel.setblocking(0)
        channel.invoke_shell()
        channel.send(self.command_start)
        time.sleep(60)
        channel.exit_status_ready()
        self.env['server.action.remote.history'].create({'server_id': self.id, 'action': 'started'})
        self.rotate_history()
        return {
            'name': 'Success',
            'view_mode': 'form',
            'res_model': 'server.action.remote.result.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_body': "Started %s successfully !!!" % self.name},
        }
    
    def action_stop_server(self):
        self.ensure_one()
        self.test_server_connection(raise_success=False)
        connection_data = self.get_server_object()
        channel = connection_data['object']
        channel.setblocking(0)
        channel.invoke_shell()
        channel.send(self.command_stop)
        time.sleep(60)
        channel.exit_status_ready()
        self.env['server.action.remote.history'].create({'server_id': self.id, 'action': 'stopped'})
        self.rotate_history()
        return {
            'name': 'Success',
            'view_mode': 'form',
            'res_model': 'server.action.remote.result.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_body': "Stopped %s successfully !!!" % self.name},
        }

    def action_restart_server(self):
        self.ensure_one()
        self.test_server_connection(raise_success=False)
        connection_data = self.get_server_object()
        channel = connection_data['object']
        channel.setblocking(0)
        channel.invoke_shell()
        channel.send(self.command_restart)
        time.sleep(60)
        channel.exit_status_ready()
        self.env['server.action.remote.history'].create({'server_id': self.id, 'action': 'restarted'})
        self.rotate_history()
        return {
            'name': 'Success',
            'view_mode': 'form',
            'res_model': 'server.action.remote.result.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_body': "Restarted %s successfully !!!" % self.name},
        }

    def action_git_pull(self):
        self.ensure_one()
        self.test_server_connection(raise_success=False)
        connection_data = self.get_server_object()
        channel = connection_data['object']
        channel.setblocking(0)
        channel.invoke_shell()
        channel.send(self.command_git_pull)
        time.sleep(120)
        channel.exit_status_ready()
        self.env['server.action.remote.history'].create({'server_id': self.id, 'action': 'pulled'})
        self.rotate_history()
        return {
            'name': 'Success',
            'view_mode': 'form',
            'res_model': 'server.action.remote.result.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_body': "Pull Git %s successfully !!!" % self.name},
        }

    def action_backup_sql(self):
        self.ensure_one()
        self.test_server_connection(raise_success=False)
        connection_data = self.get_server_object()
        channel = connection_data['object']
        channel.setblocking(0)
        channel.invoke_shell()
        channel.send(self.command_backup_sql)
        time.sleep(1800)
        channel.exit_status_ready()
        self.env['server.action.remote.history'].create({'server_id': self.id, 'action': 'backup_sql'})
        self.rotate_history()
        return {
            'name': 'Success',
            'view_mode': 'form',
            'res_model': 'server.action.remote.result.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_body': "Backup SQL %s successfully !!!" % self.name},
        }

    def action_backup_data(self):
        self.ensure_one()
        self.test_server_connection(raise_success=False)
        connection_data = self.get_server_object()
        channel = connection_data['object']
        channel.setblocking(0)
        channel.invoke_shell()
        channel.send(self.command_backup_data)
        time.sleep(1800)
        channel.exit_status_ready()
        self.env['server.action.remote.history'].create({'server_id': self.id, 'action': 'backup_data'})
        self.rotate_history()
        return {
            'name': 'Success',
            'view_mode': 'form',
            'res_model': 'server.action.remote.result.wizard',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_body': "Backup Data File %s successfully !!!" % self.name},
        }

    def rotate_history(self):
        self.ensure_one()
        rotation = self.auto_delete_history_rotation

        if len(self.history_ids) > rotation:

            unwanted = self.history_ids.sorted(key=lambda x: x.create_date, reverse=True)
            unwanted[rotation:].unlink()
