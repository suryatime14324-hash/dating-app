#!/usr/bin/env python3
import os
from app import create_app, db
from app.models import User, Profile, Like, Match, Message

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Profile': Profile,
        'Like': Like,
        'Match': Match,
        'Message': Message
    }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
