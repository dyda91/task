import os
from dotenv import load_dotenv
import logging
import sys
from datetime import datetime, timedelta
from flask import Flask, render_template, redirect, url_for, request, make_response
from models import db, Event
from forms import EventForm
from flask_migrate import Migrate
from twilio.rest import Client
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.schedulers.base import SchedulerAlreadyRunningError
from datetime import date

load_dotenv()

logging.basicConfig(stream=sys.stdout, level=logging.INFO)

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

db.init_app(app)
migrate = Migrate(app, db)

# Configurações do Twilio para o primeiro número
account_sid = os.getenv('TWILIO_ACCOUNT_SID')
auth_token = os.getenv('TWILIO_AUTH_TOKEN')
client = Client(account_sid, auth_token)
number_to = os.getenv('NUMBER_TO')
number_from = os.getenv('NUMBER_FROM')

# Configurações do Twilio para o segundo número
account_sid2 = os.getenv('TWILIO_ACCOUNT_SID2')
auth_token2 = os.getenv('TWILIO_AUTH_TOKEN2')
client2 = Client(account_sid2, auth_token2)
number_to2 = os.getenv('NUMBER_TO2')
number_from2 = os.getenv('NUMBER_FROM2')

def enviar_notificacao(evento):
    task = ["Audiência", "Recurso", "Emenda", "outros"][evento.task] if 0 <= evento.task <= 3 else "Tarefa"
    
    mensagem = (
        f"LEMBRETE:\n\n"
        f"{task} do cliente {evento.name}\n"
        f"Agendada para: {evento.date} às {evento.time}.\n\n"
        f"{evento.link}\n\n"
        f"{evento.notes}\n"
    )
    
    # Enviar notificação para o primeiro número
    try:
        message = client.messages.create(
            body=mensagem,
            from_=number_from,
            to=number_to
        )
        print(f"[SUCESSO] Mensagem enviada para '{evento.name}' no primeiro número! SID: {message.sid}")
    except Exception as e:
        print(f"[ERRO] Erro ao enviar mensagem para '{evento.name}' no primeiro número: {e}")
    
    # Enviar notificação para o segundo número, se marcado
    if evento.notify_second_number:
        try:
            message = client2.messages.create(
                body=mensagem,
                from_=number_from2,
                to=number_to2
            )
            print(f"[SUCESSO] Mensagem enviada para '{evento.name}' no segundo número! SID: {message.sid}")
        except Exception as e:
            print(f"[ERRO] Erro ao enviar mensagem para '{evento.name}' no segundo número: {e}")

def verificar_eventos():
    horario_atual = datetime.now().replace(second=0, microsecond=0)
    limite_24h = horario_atual + timedelta(days=1)
    limite_1h = horario_atual + timedelta(hours=1)

    print(f"\n[INFO] Verificação executada em: {horario_atual}")
    print(f"[INFO] Notificando eventos agendados até {limite_24h}")

    with app.app_context():
        eventos_proximos = Event.query.filter((Event.notified == False) | (Event.notified_one_hour == False)).all()

        for evento in eventos_proximos:
            try:
                evento_datetime = datetime.strptime(f"{evento.date} {evento.time}", "%Y-%m-%d %H:%M")
                tempo_ate_evento = evento_datetime - horario_atual

                print(f"\n[INFO] Verificando evento '{evento.name}'")
                print(f"  - Agendado para: {evento_datetime}")
                print(f"  - Tempo até o evento: {tempo_ate_evento}")

                # Notificação 24 horas antes
                if timedelta(hours=1) <= tempo_ate_evento <= timedelta(days=1) and not evento.notified:
                    print(f"[INFO] Enviando notificação para o evento '{evento.name}' (24 horas antes)")
                    enviar_notificacao(evento)
                    evento.notified = True
                    db.session.commit()
                
                # Notificação 1 hora antes
                elif timedelta(minutes=0) <= tempo_ate_evento <= timedelta(hours=1) and not evento.notified_one_hour:
                    print(f"[INFO] Enviando notificação para o evento '{evento.name}' (1 hora antes)")
                    enviar_notificacao(evento)
                    evento.notified_one_hour = True
                    db.session.commit()
                else:
                    print(f"[INFO] Evento '{evento.name}' fora do intervalo de notificação.")
            except Exception as e:
                print(f"[ERRO] Erro ao processar evento '{evento.name}': {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(verificar_eventos, 'interval', minutes=1)

try:
    if not scheduler.running:
        scheduler.start()
        print("[INFO] Agendador iniciado para verificar eventos a cada minuto.")
except SchedulerAlreadyRunningError:
    print("[INFO] O agendador já está em execução.")

from datetime import date


@app.route('/')
def index():
    page = request.args.get('page', 1, type=int)
    eventos = Event.query.order_by(Event.id.desc()).paginate(page=page, per_page=10)

    # Buscar eventos do dia atual
    hoje = date.today().strftime("%Y-%m-%d")
    eventos_hoje = Event.query.filter_by(date=hoje).all() or []

    # Verificar se o cookie para ocultar o popup do dia está presente
    ocultar_popup = request.cookies.get('ocultar_popup') == hoje

    form = EventForm()
    response = make_response(render_template('index.html', eventos=eventos, eventos_hoje=eventos_hoje, ocultar_popup=ocultar_popup, form=form))
    return response

# Rota para definir o cookie e ocultar o popup
@app.route('/ocultar_popup', methods=['POST'])
def ocultar_popup():
    hoje = date.today().strftime("%Y-%m-%d")
    response = make_response({"message": "Popup ocultado para o dia"})
    response.set_cookie('ocultar_popup', hoje, max_age=86400)  # Expira em 1 dia
    return response



@app.route('/add', methods=['POST'])
def add_event():
    form = EventForm()
    if form.validate_on_submit():
        data_evento = form.date.data.strftime("%Y-%m-%d")
        hora_evento = form.time.data.strftime("%H:%M")
        notify_second_number = 'notify_second_number' in request.form 

        novo_evento = Event(
            task=int(form.task.data),
            name=form.name.data,
            process_number=form.process_number.data,
            date=data_evento,
            time=hora_evento,
            situation=int(request.form.get('situation', 0)),
            link=form.link.data,
            notes=form.notes.data,
            notified=False,
            notify_second_number=notify_second_number
        )
        db.session.add(novo_evento)
        db.session.commit()
        return redirect(url_for('index'))

    eventos = Event.query.all()
    return render_template('index.html', eventos=eventos, form=form, show_modal=True)

@app.route('/update_event/<int:id>', methods=['POST'])
def update_event(id):
    evento = Event.query.get(id)
    if evento:
        nova_data = request.form['date']
        nova_hora = request.form['time']
        if evento.date != nova_data or evento.time != nova_hora:
            evento.notified = False
            evento.notified_one_hour = False  
        evento.task = request.form.get('task', 0)
        evento.name = request.form['name']
        evento.date = nova_data
        evento.process_number = request.form['process_number']
        evento.time = nova_hora
        evento.link = request.form['link']
        evento.notes = request.form['notes']
        evento.situation = request.form.get('situation', 0)
        evento.notify_second_number = 'notify_second_number' in request.form  

        db.session.commit()
    return redirect(url_for('index'))

@app.route('/delete_event/<int:id>', methods=['POST'])
def delete_event(id):
    evento = Event.query.get(id)
    if evento:
        db.session.delete(evento)
        db.session.commit()
    return redirect(url_for('index'))


if __name__ == '__main__':
    print("[INFO] Aplicação iniciada.")
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000, debug=True)
