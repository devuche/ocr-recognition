from . import db
from datetime import datetime, timedelta
import pytz

# Define the Nigerian timezone (WAT/WAST)
nigeria_timezone = pytz.timezone('Africa/Lagos')

class Documents(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    document_name = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    email = db.Column(db.String(100), nullable=False)  # email
    username = db.Column(db.String(100), nullable=False)  # username
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(nigeria_timezone))

class Conversation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(100), nullable=False, unique=True)
    user_id = db.Column(db.String(100), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    content = db.Column(db.JSON, nullable=False)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)

    document = db.relationship('Documents', backref=db.backref('conversations', lazy=True))
    @classmethod
    def update_access_time(self):
        self.accessed_at = datetime.utcnow()
        db.session.commit()

    def clear_expired_conversations(cls):
        expiration_time = datetime.utcnow() - timedelta(hours=0.5)
        expired_conversations = cls.query.filter(cls.accessed_at < expiration_time).all()
        for conversation in expired_conversations:
            db.session.delete(conversation)
            db.session.commit()