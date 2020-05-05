from datetime import datetime
import uuid
import json
import sys
from app import db
from flask import jsonify, abort, request, make_response, url_for, render_template, Response
from flask_classy import FlaskView
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import synonym, relationship
from sqlalchemy import Table, Column, Integer, ForeignKey
from sqlalchemy import UniqueConstraint

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    snippet_id = Column(Integer, ForeignKey('snippet.id'))
    snippet = relationship("Snippet", back_populates="logs")
    entry = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, entry, snippet):
        super(Log, self).__init__()
        self.entry = entry
        self.snippet = snippet

class Snippet(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(255), nullable=False)
    lineno = db.Column(db.Integer)
    _snppt = db.Column('snppt', db.String(255), nullable=False)
    _status = db.Column('status', db.String(1), default='u', nullable=False)
    logs = relationship("Log", back_populates="snippet")
    __table_args__ = (UniqueConstraint('fname', 'lineno', name='_fname_lineno_uc'), )

    def __init__(self, *args, **kwargs):
        super(Snippet, self).__init__()
        self.id = kwargs.get('id', None)
        self.snppt = kwargs.get('snippet')
        self.status = kwargs.get('status', '')



    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return "<snippet('%s', '%s', '%s', '%s', '%s')>" % (self.id, self.fname, self.lineno, self.snppt, self.status)

    @property
    def snppt(self):
        return self._snppt

    @snppt.setter
    def snppt(self, v):
        lentry = "snippet('%s' -> '%s')" % (self._snppt, v)
        l = Log(lentry, snippet=self)
        db.session.add(l)
        self._snppt = v

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, v):
        lentry = "status('%s' -> '%s')" % (self._status, v)
        l = Log(lentry, snippet=self)
        db.session.add(l)
        self._status = v

    snppt = synonym('_snppt', descriptor=snppt)
    status = synonym('_status', descriptor=status)

    def save(self):
        db.session.add(self)
        db.session.commit()


class SnippetsView(FlaskView):
    __cache = {}
    def index(self):
        entry = Snippet.query.filter(Snippet.status=='').first()
        if entry is None:
            return make_response(jsonify(status='No result found'), 404)
        entry.status = 'p'
        entry.token = uuid.uuid4().hex
        entry.save()
        SnippetsView.__cache[entry.id] = entry
        return jsonify(snippet=entry.snppt, id=entry.id, status=entry.status, token=entry.token)

    def monitor(self):
        processing = Snippet.query.filter(Snippet.status=='p')
        completed = Snippet.query.filter(Snippet.status=='y')
        outstanding = Snippet.query.filter(Snippet.status=='')

        html = render_template('monitor.html', title='Monitor', processing=processing, completed=completed, outstanding=outstanding)
        r = make_response(html)
        r.mimetype = "text/html"
        return r

    def patch(self, id):
        try:
            id = int(id)
        except ValueError:
            return make_response(jsonify(status='A number was required.'), 400)
        entry = SnippetsView.__cache.get(id, None)
        if not entry:
            return make_response(jsonify(status='Can not update an item which has not been requested'), 400)
        if 'status' not in request.json:
            return make_response(jsonify(status='expected status variable'), 400)
        if request.json['status'] not in ['y', 'n']:
            return make_response(jsonify(status='Unexpected status, should be one of: y, n'), 400)
        if 'token' not in request.json:
            return make_response(jsonify(status='expected token variable'), 400)
        token = request.json['token']
        if entry.token != token:
            return make_response(jsonify(status='token does not match, you are not authorized'), 403)
        entry.status = request.json['status']
        audio = base64.decodestring(request.json['audio'])
        wf = wave.open('/tmp/%s-%s.wav' %(entry.fname, entry.lineno), 'wb')
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(16000)
        wf.writeframes(audio)
        wf.close()
        entry.save()
        SnippetsView.__cache.pop(entry.id)
        return jsonify(snippet=entry.snppt, id=entry.id, status=entry.status)

    def post(self):
        snippet = request.json['snippet']
        if snippet == "":
            return make_response(jsonify(status='snippet can not be empty.'), 400)
        try:
            entry = Snippet(snippet=snippet)
            entry.fname = request.json['fname']
            entry.lineno = request.json['lineno']
            entry.save()
            return make_response(jsonify(fname=entry.fname, lineno=entry.lineno, snippet=entry.snppt, id=entry.id, status=entry.status), 201)
        except IntegrityError:
            return make_response(jsonify(status='fname, lineno needs to be unique'), 409)

    def reset(self):
        for entry in Snippet.query.all():
            entry.status = ''
            entry.save()
        return jsonify(status='ok')

    def shutdown(self):
        # clear our local cache:
        tmp = {}
        for id,entry in SnippetsView.__cache.items():
            tmp[id] = entry
        for id,entry in tmp.items():
            entry.status = ''
            entry.save()
            SnippetsView.__cache.pop(id)
        # get on with actually shutting down:
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()
        return jsonify(status='ok')


class LogsView(FlaskView):
    def index(self):
        return "need a snippet id"

    def get(self, id):
        p = Snippet.query.filter(Snippet.id==id).one()

        html = render_template('logs.html', title='Logs', logs=p.logs)
        r = make_response(html)
        r.mimetype = "text/html"
        return r

