import MetaTrader5 as mt5
import telegram
from telegram.request import HTTPXRequest
import schedule
import time
from datetime import datetime
import asyncio

# ---  CONFIGURACIÓN OBLIGATORIA ---
# Reemplaza estos valores con tus datos reales.

# 1. Telegram
TELEGRAM_BOT_TOKEN = 'AQUÍ_VA_TU_BOT_TOKEN_DE_BOTFATHER'
TELEGRAM_CHAT_ID = 'AQUÍ_VA_TU_CHAT_ID'  # Ejemplo: '-1001234567890'

# 2. MetaTrader 5
MT5_LOGIN = 12345678  # Tu número de cuenta de MT5
MT5_PASSWORD = 'tu_contraseña'
MT5_SERVER = 'NombreDelServidorDeTuBroker'

# --- INICIALIZACIÓN DEL BOT ---
try:
    # Configuración de red mejorada para mayor robustez.
    # Aumentamos el número de conexiones simultáneas y el tiempo de espera.
    # Esto ayuda a prevenir errores de 'Pool Timeout' en redes inestables.
    request_settings = HTTPXRequest(connection_pool_size=20, read_timeout=10.0, connect_timeout=10.0)
    bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN, request=request_settings)
    print("✅ Bot de Telegram inicializado correctamente con configuración de red mejorada.")
except Exception as e:
    print(f"❌ Error inicializando el bot de Telegram: {e}")
    exit()

# --- FUNCIONES PRINCIPALES ---

def conectar_mt5():
    """Inicializa y establece la conexión con la terminal de MetaTrader 5."""
    if not mt5.initialize(login=MT5_LOGIN, password=MT5_PASSWORD, server=MT5_SERVER):
        print(f"❌ Error en initialize(): {mt5.last_error()}")
        return False
    
    account_info = mt5.account_info()
    if account_info is None:
        print(f"❌ No se pudo obtener la información de la cuenta: {mt5.last_error()}")
        return False
        
    print(f"✅ Conexión exitosa a la cuenta MT5 #{account_info.login} en {account_info.server}")
    return True

async def notificar_operacion_abierta():
    """
    Consulta las operaciones abiertas en MT5 y envía una notificación 
    a Telegram con los datos de la operación más reciente.
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Consultando operaciones abiertas...")
    try:
        # Obtener todas las posiciones abiertas
        posiciones = mt5.positions_get()

        if posiciones is None or len(posiciones) == 0:
            print("ℹ️ No se encontraron operaciones abiertas en este momento.")
            # Opcional: podrías enviar un mensaje indicando que no hay operaciones.
            # await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="ℹ️ No hay operaciones abiertas para notificar.")
            return

        # Seleccionamos la última posición de la lista (normalmente la más reciente)
        ultima_posicion = posiciones[-1]

        # Extraemos los datos de la posición
        simbolo = ultima_posicion.symbol
        precio_entrada = ultima_posicion.price_open
        stop_loss = ultima_posicion.sl if ultima_posicion.sl > 0 else "No definido"
        take_profit = ultima_posicion.tp if ultima_posicion.tp > 0 else "No definido"
        
        # Determinamos el tipo de operación (Compra o Venta)
        if ultima_posicion.type == mt5.ORDER_TYPE_BUY:
            tipo_operacion = "🟢 COMPRA (BUY)"
        elif ultima_posicion.type == mt5.ORDER_TYPE_SELL:
            tipo_operacion = "🔴 VENTA (SELL)"
        else:
            tipo_operacion = "Desconocido"

        # Formateamos los precios para que se vean bien
        precio_entrada_str = f"`{precio_entrada:.5f}`"
        sl_str = f"`{stop_loss:.5f}`" if isinstance(stop_loss, float) else stop_loss
        tp_str = f"`{take_profit:.5f}`" if isinstance(take_profit, float) else take_profit
            
        mensaje = (
            f"🔔 **Notificación de Operación Abierta** | {datetime.now().strftime('%H:%M')}\n\n"
            f"**Activo:** `{simbolo}`\n"
            f"**Operación:** {tipo_operacion}\n"
            f"**Precio de Entrada:** {precio_entrada_str}\n\n"
            f"📈 **Take Profit (TP):** {tp_str}\n"
            f"🛑 **Stop Loss (SL):** {sl_str}\n\n"
            f"_Esta es una operación actualmente abierta en la cuenta._"
        )
        
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensaje, parse_mode='Markdown')
        print(f"✅ Notificación de la operación #{ultima_posicion.ticket} para {simbolo} enviada exitosamente.")

    except Exception as e:
        print(f"❌ Ocurrió un error al consultar las operaciones: {e}")
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=f"🤖 Hubo un error interno al intentar consultar las operaciones abiertas.")

async def enviar_mensaje_personalizado_tipo_1():
    """Envía el primer tipo de mensaje personalizado."""
    mensaje = "📈 **Actualización de Mercado.** Manténganse atentos a las oportunidades y no olviden gestionar su riesgo. ¡Seguimos operando!"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensaje)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Mensaje personalizado tipo 1 enviado.")

async def enviar_mensaje_personalizado_tipo_2():
    """Envía el segundo tipo de mensaje personalizado."""
    mensaje = "📊 **Resumen de la Sesión.** El día de trading está concluyendo. Es momento de analizar los resultados y prepararse para la siguiente jornada. ¡Buenas noches!"
    await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text=mensaje)
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Mensaje personalizado tipo 2 enviado.")

def programar_tareas():
    """Configura todas las tareas programadas con sus respectivos horarios."""
    
    def run_async_job(job_func):
        asyncio.create_task(job_func())

    # 1. Programar las 12 notificaciones (de 8:00 a 19:00 inclusive)
    #    Ahora llamará a la nueva función que consulta operaciones reales
    for hora in range(8, 20):
        schedule.every().day.at(f"{hora:02d}:00").do(run_async_job, notificar_operacion_abierta)

    # 2. Programar mensajes personalizados tipo 1 (3 veces al día)
    schedule.every().day.at("09:00").do(run_async_job, enviar_mensaje_personalizado_tipo_1)
    schedule.every().day.at("12:30").do(run_async_job, enviar_mensaje_personalizado_tipo_1)
    schedule.every().day.at("19:00").do(run_async_job, enviar_mensaje_personalizado_tipo_1)

    # 3. Programar mensajes personalizados tipo 2 (2 veces al día)
    schedule.every().day.at("12:00").do(run_async_job, enviar_mensaje_personalizado_tipo_2)
    schedule.every().day.at("21:00").do(run_async_job, enviar_mensaje_personalizado_tipo_2)

    print("🕒 Todas las tareas han sido programadas.")
    print("--- HORARIO DE TAREAS ---")
    for job in schedule.jobs:
        print(f"- {job}")
    print("-------------------------")


# --- BUCLE DE EJECUCIÓN ASÍNCRONO ---
async def main():
    if conectar_mt5():
        programar_tareas()
        print("\n🚀 Bot en funcionamiento. Esperando horarios programados...")
        await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🤖 **¡El Bot de Señales se ha iniciado correctamente!**\n\nConsultaré las operaciones abiertas y enviaré notificaciones según el horario establecido.")
        while True:
            schedule.run_pending()
            await asyncio.sleep(1) 
    else:
        print("\n🔴 El script no se ejecutará debido a un fallo en la conexión con MetaTrader 5.")
        try:
            await bot.send_message(chat_id=TELEGRAM_CHAT_ID, text="🔴 **¡Error Crítico!**\nNo se pudo establecer conexión con la cuenta de MetaTrader 5. Por favor, revise las credenciales y asegúrese de que la terminal esté abierta.")
        except Exception as e:
            print(f"No se pudo enviar notificación de error a Telegram: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 Bot detenido manually.")
    except Exception as e:
        print(f"\n❌ Ha ocurrido un error inesperado: {e}")
