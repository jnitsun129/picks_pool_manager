from flask import Flask, request, jsonify, render_template
from preweek_gather import gather_run
from preweek_template import preweek_template_run
from postweek import postweek_run

app = Flask(__name__, template_folder='../templates')


@app.route('/preweek_gather/<int:week_number>', methods=['GET'])
def preweek_gather(week_number):
    gather_run(week_number)
    return jsonify({"message": f"Form sent for week {week_number}"}), 200


@app.route('/preweek_create/<int:week_number>', methods=['GET'])
def preweek_create(week_number):
    preweek_template_run(week_number)
    return jsonify({"message": f"Picks sent for week {week_number}"}), 200


@app.route('/postweek/<int:week_number>', methods=['GET'])
def postweek(week_number):
    postweek_run(week_number)
    return jsonify({"message": f"Results sent for week {week_number}"}), 200


@app.route('/', methods=['GET'])
def operations():
    host_with_port = request.host
    return render_template('interface_template.html', host_with_port=host_with_port)


if __name__ == '__main__':
    app.run(debug=True)
