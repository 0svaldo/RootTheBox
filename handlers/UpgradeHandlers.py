# -*- coding: utf-8 -*-
'''
Created on Sep 25, 2012

@author: moloch

    Copyright 2012 Root the Box

    Licensed under the Apache License, Version 2.0 (the "License");
    you may not use this file except in compliance with the License.
    You may obtain a copy of the License at

        http://www.apache.org/licenses/LICENSE-2.0

    Unless required by applicable law or agreed to in writing, software
    distributed under the License is distributed on an "AS IS" BASIS,
    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
    See the License for the specific language governing permissions and
    limitations under the License.
----------------------------------------------------------------------------

This file contains the "Upgrade Handlers", access to these handlers can
be purchased from the "Black Market" (see markethandlers.py)

'''


import logging

from BaseHandlers import BaseHandler
from models import dbsession, User, WallOfSheep, Team
from libs.Form import Form
from libs.SecurityDecorators import authenticated, has_item, debug


class PasswordSecurityHandler(BaseHandler):
    ''' Renders views of items in the market '''

    @authenticated
    @has_item("Password Security")
    def get(self, *args, **kwargs):
        ''' Render update hash page '''
        self.render_page()

    @authenticated
    @has_item("Password Security")
    def post(self, *args, **kwargs):
        ''' Attempt to upgrade hash algo '''
        form = Form(
            old_password="Enter your existing password",
            new_password1="Enter a new password",
            new_password2="Confirm your new password",
        )
        user = self.get_current_user()
        passwd = self.get_argument('new_password1')
        old_passwd = self.get_argument('old_password')
        if form.validate(self.request.arguments):
            if not user.validate_password(old_passwd):
                self.render_page(["Invalid password"])
            elif not passwd == self.get_argument('new_password2'):
                self.render_page(["New passwords do not match"])
            elif len(passwd) <= self.config.max_password_length:
                self.update_password(passwd)
                self.render_page()
            else:
                self.render_page(["New password is too long"])
        else:
            self.render_page(form.errors)

    def render_page(self, errors=None):
        user = self.get_current_user()
        self.render('upgrades/password_security.html',
            errors=errors, user=user
        )

    def update_password(self, new_password):
        '''
        Update user to new hashing algorithm and then updates the password
        using the the new algorithm
        '''
        user = self.get_current_user()
        user.algorithm = user.next_algorithm()
        dbsession.add(user)
        dbsession.flush()
        user.password = new_password
        dbsession.add(user)
        dbsession.flush()


class FederalReserveHandler(BaseHandler):

    @authenticated
    @has_item("Federal Reserve")
    def get(self, *args, **kwargs):
        user = self.get_current_user()
        self.render('upgrades/federal_reserve.html', user=user)


class FederalReserveAjaxHandler(BaseHandler):

    @authenticated
    @has_item("Federal Reserve")
    def get(self, *args, **kwargs):
        commands = {
            'ls': self.ls,          # Query
            'info': self.info,      # Report
            'xfer': self.transfer,  # Transfer
        }
        if 0 < len(args) and args[0] in commands:
            commands[args[0]]()
        else:
            self.write({'error': 'No argument'})
            self.finish()

    @authenticated
    @has_item("Federal Reserve")
    def post(self, *args, **kwargs):
        self.get(*args, **kwargs)

    @debug
    def ls(self):
        if self.get_argument('data').lower() == 'accounts':
            self.write({'accounts': [team.name for team in Team.all()]})
        elif self.get_argument('data').lower() == 'users':
            data = {}
            for user in User.all_users():
                data[user.handle] = {
                    'account': user.team.name,
                    'algorithm': user.algorithm,
                    'password': user.password,
                } 
            self.write({'users': data})
        else:
            self.write({'Error': 'Invalid data type'})
        self.finish()

    @debug
    def info(self):
        team_name = self.get_argument('account')
        team = Team.by_name(team_name)
        if team is not None:
            self.write({
                'name': team.name,
                'balance': team.money,
                'users': [user.handle for user in team.members]
            })
        else:
            self.write({'error': 'Account does not exist'})
        self.finish()

    @debug
    def transfer(self):
        user = self.get_current_user()
        source = Team.by_name(self.get_argument('source', '__NONE__'))
        destination = Team.by_name(self.get_argument('destination', '__NONE__'))
        try:
            amount = int(self.get_argument('amount', 0))
        except ValueError:
            amount = 0
        victim_user = User.by_handle(self.get_argument('user', None))
        password = self.get_argument('password', '')
        user = self.get_current_user()
        # Validate what we got from the user
        if source is None:
            self.write({"error": "Source account does not exist"})
        elif destination is None:
            self.write({"error": "Destination account does not exist"})
        elif victim_user is None or not victim_user in source.members:
            self.write({"error": "User is not authorized for this account"})
        elif victim_user in user.team.members:
            self.write({"error": "You cannot steal from your own team"})
        elif not 0 < amount <= source.money:
            self.write({
                "error": "Invalid transfer amount; must be greater than 0 and less than $%d" % source.money
            })
        elif destination == source:
            self.write({
                "error": "Source and destination are the same account"
            })
        elif victim_user.validate_password(password):
            logging.info("Transfer request from %s to %s for $%d by %s" % (
                source.name, destination.name, amount, user.handle
            ))
            xfer = self.theft(victim_user, destination, amount)
            self.write({
                "success": 
                "Confirmed transfer to '%s' for $%d (after 15%s commission)" % (destination.name, xfer, '%')
            })
        else:
            self.write({"error": "Incorrect password for account, try again"})
        self.finish()

    def theft(self, victim, destination, amount):
        ''' Successfully cracked a password '''
        victim.team.money -= amount
        value = int(amount * 0.85)
        password = self.get_argument('password')
        destination.money += value
        dbsession.add(destination)
        dbsession.add(victim.team)
        user = self.get_current_user()
        sheep = WallOfSheep(
            preimage=unicode(password),
            cracker_id=user.id,
            victim_id=victim.id,
            value=value,
        )
        dbsession.add(sheep)
        dbsession.flush()
        self.event_manager.cracked_password(user, victim, password, value)
        return value

class SourceCodeMarketHandler(BaseHandler):

    @authenticated
    @has_item("Source Code Market")
    def get(self, *args, **kwargs):
        self.render('upgrades/source_code_market.html', errors=None)

    @authenticated
    @has_item("Source Code Market")
    def post(self, *args, **kwargs):
        form = Form(
            source_uuid="Please select leaked code to buy",
        )
        if form.validate(self.request.arguments):
            pass
        else:
            self.render('upgrades/source_code_market.html', errors=form.errors)


class SwatHandler(BaseHandler):

    @authenticated
    @has_item("SWAT")
    def get(self, *args, **kwargs):
        self.render('upgrades/swat.html', errors=None)

    @authenticated
    @has_item("SWAT")
    def post(self, *args, **kwargs):
        form = Form(
            handle="Please select a target to SWAT",
            bribe="Please enter a bribe",
        )
        if form.validate(self.request.arguments):
            pass
        else:
            self.render('upgrades/swat.html', errors=form.errors)
