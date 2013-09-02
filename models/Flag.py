# -*- coding: utf-8 -*-
'''
Created on Mar 12, 2012

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
'''


import re
import hashlib
import xml.etree.cElementTree as ET

from uuid import uuid4
from sqlalchemy import Column, ForeignKey
from sqlalchemy.types import Unicode, Integer, Boolean, String
from models import dbsession, Box
from models.BaseGameObject import BaseObject


class Flag(BaseObject):
    ''' Flag definition '''

    name = Column(Unicode(32), nullable=False)
    uuid = Column(String(36), unique=True, nullable=False, default=lambda: str(uuid4()))
    token = Column(Unicode(256), nullable=False)
    description = Column(Unicode(256), nullable=False)
    value = Column(Integer, nullable=False)
    is_file = Column(Boolean, default=False)
    is_case_sensitive = Column(Boolean, default=True)
    box_id = Column(Integer, ForeignKey('box.id'), nullable=False)

    @classmethod
    def all(cls):
        ''' Returns a list of all objects in the database '''
        return dbsession.query(cls).all()

    @classmethod
    def by_id(cls, ident):
        ''' Returns a the object with id of ident '''
        return dbsession.query(cls).filter_by(id=ident).first()

    @classmethod
    def by_name(cls, fname):
        ''' Returns a the object with name of fname '''
        return dbsession.query(cls).filter_by(name=unicode(fname)).first()

    @classmethod
    def by_uuid(cls, uuid):
        ''' Return and object based on a uuid '''
        return dbsession.query(cls).filter_by(uuid=unicode(uuid)).first()

    @classmethod
    def by_token(cls, token):
        ''' Return and object based on a token '''
        return dbsession.query(cls).filter_by(token=unicode(token)).first()

    @classmethod
    def digest(self, data):
        ''' Token is SHA1 of data '''
        sha = hashlib.sha1()
        sha.update(data)
        return unicode(sha.hexdigest())

    @property
    def box(self):
        return Box.by_id(self.box_id)

    @property
    def game_level(self):
        return self.box.game_level

    def capture(self, token):
        if self.is_file:
            return self.token == token
        else:
            pattern = re.compile(self.token)
            return pattern.match(token) is not None

    def to_xml(self, parent):
        ''' Write attributes to XML doc '''
        flag_elem = ET.SubElement(parent, "flag")
        flag_elem.set("isfile", str(self.is_file))
        ET.SubElement(flag_elem, "name").text = str(self.name)
        ET.SubElement(flag_elem, "token").text = str(self.token)
        ET.SubElement(flag_elem, "description").text = str(self.description)
        ET.SubElement(flag_elem, "value").text = str(self.value)

    def to_dict(self):
        ''' Returns public data as a dict '''
        box = Box.by_id(self.box_id)
        return {
            'name': self.name,
            'uuid': self.uuid,
            'description': self.description,
            'value': self.value,
            'box': box.uuid,
            'token': self.token,
        }

    def __str__(self):
        return self.name.encode('ascii', 'ignore')

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return "<Flag - name:%s, is_file:%s >" % (
            self.name, str(self.is_file)
        )
