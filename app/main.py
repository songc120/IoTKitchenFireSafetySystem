from flask import Blueprint, render_template
from flask_login import login_required
from pubnub.pnconfiguration import PNConfiguration
from pubnub.pubnub import PubNub
from .decorators import admin_required

main = Blueprint('main', __name__)

pnconfig = PNConfiguration()
pnconfig.subscribe_key = "sub-c-7c1de1d9-ea5b-451f-bb88-35ae502a81c4"
pnconfig.publish_key = "pub-c-85ba3694-4855-4861-a14b-fdfcb90cf839"
pnconfig.uuid = "server"
pubnub = PubNub(pnconfig)

@main.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@main.route('/api/reset_alarm', methods=['POST'])
@login_required
@admin_required
def reset_alarm():
    pubnub.publish().channel("chenweisong728").message({
        "reset_alarm": "True"
    }).sync()
    return {"status": "success"} 