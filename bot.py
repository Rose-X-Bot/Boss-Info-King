import os
import logging
import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler, ContextTypes
from telegram.error import TelegramError

# Bot Configuration - Render environment variables से लो
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8173036082:AAHlrHaHnaXKNbQl7v3wm-y0djPP6ezFEV0')

# API URLs
NUMBER_API = "https://api.x10.network/numapi.php?action=api&key=thakurji&number="
VEHICLE_API = "https://vehicle-to-own-num.vercel.app/vehicle?owner="
PINCODE_API = "https://pin-code-2-village.vercel.app/?pin="
AADHAR_API = "https://api.x10.network/numapi.php?action=api&key=thakurji&aadhar="

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Format Mobile Number Information
def format_mobile_info(data, mobile_number):
    """Format mobile number information beautifully."""
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        if not data.get("success", False):
            return "❌ No information found for this mobile number."
        
        results = data.get("result", [])
        if not results:
            return "📱 No information available for this number."
        
        formatted_text = f"📱 *MOBILE NUMBER INFORMATION*\n"
        formatted_text += f"────────────────────────\n"
        formatted_text += f"🔍 *Searched Number:* `{mobile_number}`\n\n"
        
        for i, result in enumerate(results, 1):
            formatted_text += f"*📍 Result {i}:*\n"
            formatted_text += f"├─ 📛 *Name:* {result.get('name', 'N/A')}\n"
            formatted_text += f"├─ 📞 *Mobile:* `{result.get('mobile', 'N/A')}`\n"
            
            father_name = result.get('father_name', 'N/A')
            if father_name and father_name.lower() != 'null':
                formatted_text += f"├─ 👨‍👦 *Father:* {father_name}\n"
            
            alt_mobile = result.get('alt_mobile', 'N/A')
            if alt_mobile and alt_mobile.lower() != 'null':
                formatted_text += f"├─ 📱 *Alt Mobile:* `{alt_mobile}`\n"
            
            address = result.get('address', 'N/A')
            if address and address.lower() != 'null':
                # Clean address formatting
                address = address.replace('!', '\n   ').replace('/', '')
                formatted_text += f"├─ 🏠 *Address:*\n   {address}\n"
            
            circle = result.get('circle', 'N/A')
            if circle and circle.lower() != 'null':
                formatted_text += f"├─ 📡 *Circle:* {circle}\n"
            
            id_number = result.get('id_number', 'N/A')
            if id_number and id_number.lower() != 'null':
                formatted_text += f"├─ 🆔 *ID Number:* `{id_number}`\n"
            
            email = result.get('email', 'N/A')
            if email and email.lower() != 'null':
                formatted_text += f"└─ 📧 *Email:* {email}\n"
            else:
                formatted_text += f"└─ 📧 *Email:* Not Available\n"
            
            formatted_text += f"\n"
        
        return formatted_text
        
    except Exception as e:
        logger.error(f"Error formatting mobile info: {str(e)}")
        return f"❌ Error formatting mobile info: {str(e)}"

# Format Vehicle Information
def format_vehicle_info(data, vehicle_number):
    """Format vehicle information beautifully."""
    try:
        if isinstance(data, str):
            # Try to parse as JSON first
            try:
                data = json.loads(data)
                # If it's a JSON object with success field
                if isinstance(data, dict):
                    return format_vehicle_json(data, vehicle_number)
            except:
                pass
            
            # If not JSON or different format, show raw but formatted
            lines = data.strip().split('\n')
            formatted_text = f"🚗 *VEHICLE INFORMATION*\n"
            formatted_text += f"──────────────────────\n"
            formatted_text += f"*Vehicle Number:* `{vehicle_number.upper()}`\n\n"
            
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    formatted_text += f"*{key.strip()}:* {value.strip()}\n"
                elif line.strip():
                    formatted_text += f"{line.strip()}\n"
            
            return formatted_text
        
        return format_vehicle_json(data, vehicle_number)
        
    except Exception as e:
        logger.error(f"Error formatting vehicle info: {str(e)}")
        return f"❌ Error formatting vehicle info: {str(e)}"

def format_vehicle_json(data, vehicle_number):
    """Format vehicle JSON data."""
    formatted_text = f"🚗 *VEHICLE INFORMATION*\n"
    formatted_text += f"──────────────────────\n"
    formatted_text += f"*Vehicle Number:* `{vehicle_number.upper()}`\n\n"
    
    if isinstance(data, dict):
        for key, value in data.items():
            if value and str(value).lower() != 'null' and str(value).strip():
                formatted_text += f"*{key.replace('_', ' ').title()}:* {value}\n"
    
    return formatted_text

# Format PIN Code Information - UPDATED FOR CLEAN DISPLAY
def format_pincode_info(data, pincode):
    """Format PIN code information beautifully."""
    try:
        formatted_text = f"📬 *PIN CODE INFORMATION*\n"
        formatted_text += f"───────────────────────\n"
        formatted_text += f"*PIN Code:* `{pincode}`\n\n"
        
        if isinstance(data, str):
            try:
                # Try to parse as JSON
                data = json.loads(data)
            except json.JSONDecodeError:
                # If not JSON, return as is
                return f"📬 *PIN CODE INFORMATION*\n───────────────────────\n*PIN Code:* `{pincode}`\n\n{data}"
        
        # Check if data is a dictionary
        if isinstance(data, dict):
            # Add summary information
            status = data.get('status', 'N/A')
            count = data.get('count', 0)
            searched_pin = data.get('searchedpin') or data.get('searched_pin', pincode)
            
            formatted_text += f"*Status:* {status}\n"
            formatted_text += f"*Total Offices:* {count}\n"
            formatted_text += f"*Searched PIN:* {searched_pin}\n\n"
            
            # Add offices information
            offices = data.get('offices', [])
            if offices:
                formatted_text += f"*📮 POST OFFICES IN THIS AREA:*\n\n"
                
                for i, office in enumerate(offices, 1):
                    formatted_text += f"*🏢 Office {i}: {office.get('name', 'N/A')}*\n"
                    formatted_text += f"├─ *Type:* {office.get('branchType', 'N/A')}\n"
                    formatted_text += f"├─ *Block:* {office.get('block', 'N/A')}\n"
                    formatted_text += f"├─ *District:* {office.get('district', 'N/A')}\n"
                    formatted_text += f"├─ *State:* {office.get('state', 'N/A')}\n"
                    formatted_text += f"├─ *Delivery Status:* {office.get('deliveryStatus', 'N/A')}\n"
                    formatted_text += f"└─ *Division:* {office.get('division', 'N/A')}\n\n"
                    
                    # If text is getting too long, add a continuation marker
                    if len(formatted_text) > 3000 and i < len(offices):
                        remaining = len(offices) - i
                        formatted_text += f"*...and {remaining} more offices.*\n"
                        break
                
                formatted_text += f"📍 *Total {len(offices)} offices found for PIN code {pincode}*"
            else:
                formatted_text += "*No post offices found for this PIN code.*"
        
        else:
            formatted_text += f"{str(data)}"
        
        return formatted_text
        
    except Exception as e:
        logger.error(f"Error formatting pincode: {str(e)}")
        return f"📬 *PIN CODE INFORMATION*\n───────────────────────\n*PIN Code:* `{pincode}`\n\n{str(data)[:2000]}"

# Format Aadhar Information
def format_aadhar_info(data, aadhar_number):
    """Format Aadhar information beautifully."""
    try:
        if isinstance(data, str):
            data = json.loads(data)
        
        if not data.get("success", False):
            return "❌ No information found for this Aadhar number."
        
        results = data.get("result", [])
        if not results:
            return "🆔 No information available for this Aadhar number."
        
        formatted_text = f"🆔 *AADHAR INFORMATION*\n"
        formatted_text += f"─────────────────────\n"
        formatted_text += f"*Aadhar Number:* `{aadhar_number}`\n\n"
        
        for i, result in enumerate(results, 1):
            formatted_text += f"*📍 Result {i}:*\n"
            
            for key, value in result.items():
                if value and str(value).lower() != 'null':
                    key_name = key.replace('_', ' ').title()
                    if key in ['mobile', 'alt_mobile', 'id_number']:
                        formatted_text += f"├─ *{key_name}:* `{value}`\n"
                    elif key == 'address':
                        # Clean address formatting
                        address = str(value).replace('!', '\n   ').replace('/', '')
                        formatted_text += f"├─ *{key_name}:*\n   {address}\n"
                    else:
                        formatted_text += f"├─ *{key_name}:* {value}\n"
            
            formatted_text += f"\n"
        
        return formatted_text
        
    except Exception as e:
        logger.error(f"Error formatting Aadhar info: {str(e)}")
        return f"❌ Error formatting Aadhar info: {str(e)}"

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message when the command /start is issued."""
    try:
        user = update.effective_user
        welcome_message = f"""
👋 Hello {user.first_name}!

🤖 *INFORMATION BOT*
─────────────────

I can extract information from:

📱 *Mobile Number* - Send 10-digit number
🚗 *Vehicle Number* - Send vehicle number
📬 *PIN Code* - Send 6-digit PIN code
🆔 *Aadhar Number* - Send 12-digit number

*Examples:*
• `6395954711` - Mobile Info
• `up26r4007` - Vehicle Info  
• `262124` - PIN Code Info
• `123412341234` - Aadhar Info

Choose an option below or simply send the information!
"""
        
        keyboard = [
            [InlineKeyboardButton("📱 Mobile Info", callback_data='type_mobile')],
            [InlineKeyboardButton("🚗 Vehicle Info", callback_data='type_vehicle')],
            [InlineKeyboardButton("📬 PIN Code Info", callback_data='type_pincode')],
            [InlineKeyboardButton("🆔 Aadhar Info", callback_data='type_aadhar')]
        ]
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            welcome_message,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in start command: {str(e)}")

# Button callback handler
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    try:
        query = update.callback_query
        await query.answer()
        
        data = query.data
        
        if data == 'type_mobile':
            message = "📱 *Mobile Number Information*\n\nSend a 10-digit mobile number\n\n*Example:* `6395954711`"
        elif data == 'type_vehicle':
            message = "🚗 *Vehicle Information*\n\nSend vehicle registration number\n\n*Example:* `up26r4007`"
        elif data == 'type_pincode':
            message = "📬 *PIN Code Information*\n\nSend a 6-digit PIN code\n\n*Example:* `262124`"
        elif data == 'type_aadhar':
            message = "🆔 *Aadhar Information*\n\nSend a 12-digit Aadhar number\n\n*Example:* `123412341234`"
        
        await query.edit_message_text(
            text=message,
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Error in button callback: {str(e)}")

# Function to detect input type
def detect_input_type(text):
    """Detect the type of input based on the text."""
    text = text.strip().lower()
    
    # Check for mobile number (10 digits)
    if text.isdigit() and len(text) == 10:
        return 'mobile'
    
    # Check for Aadhar number (12 digits)
    elif text.isdigit() and len(text) == 12:
        return 'aadhar'
    
    # Check for PIN code (6 digits)
    elif text.isdigit() and len(text) == 6:
        return 'pincode'
    
    # Check for vehicle number (alphanumeric, typically 8-10 characters)
    # Remove spaces and special characters
    clean_text = ''.join(c for c in text if c.isalnum())
    if (any(char.isalpha() for char in clean_text) and 
        any(char.isdigit() for char in clean_text) and
        5 <= len(clean_text) <= 15):
        return 'vehicle'
    
    else:
        return 'unknown'

# Function to fetch and format data from APIs
async def fetch_and_format_data(input_text, input_type):
    """Fetch data from API and format it beautifully."""
    try:
        if input_type == 'mobile':
            url = NUMBER_API + input_text
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            return format_mobile_info(response.text, input_text)
        
        elif input_type == 'vehicle':
            url = VEHICLE_API + input_text
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            return format_vehicle_info(response.text, input_text)
        
        elif input_type == 'pincode':
            url = PINCODE_API + input_text
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            return format_pincode_info(response.text, input_text)
        
        elif input_type == 'aadhar':
            url = AADHAR_API + input_text
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            return format_aadhar_info(response.text, input_text)
        
        else:
            return "❌ *Invalid Input Format*\n\nPlease check the format and try again."
    
    except requests.exceptions.Timeout:
        return "⏳ *Request Timeout*\n\nThe API is taking too long to respond. Please try again later."
    except requests.exceptions.RequestException as e:
        logger.error(f"API Request Error: {str(e)}")
        return f"❌ *Network Error*\n\nCould not connect to the server. Please try again."
    except Exception as e:
        logger.error(f"Unexpected Error in fetch_and_format_data: {str(e)}")
        return f"❌ *Error*\n\nAn unexpected error occurred."

# Handle messages with proper long message splitting
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    try:
        user_input = update.message.text.strip()
        
        # Detect input type
        input_type = detect_input_type(user_input)
        
        if input_type == 'unknown':
            await update.message.reply_text(
                "❌ *Invalid Format!*\n\n"
                "Please send:\n"
                "• 📱 10-digit Mobile Number\n"
                "• 🚗 Vehicle Number\n"
                "• 📬 6-digit PIN Code\n"
                "• 🆔 12-digit Aadhar Number\n\n"
                "Use /start to see examples.",
                parse_mode='Markdown'
            )
            return
        
        # Send processing message
        processing_msg = await update.message.reply_text(
            f"⏳ *Processing...*\n\n"
            f"Fetching information for: `{user_input}`",
            parse_mode='Markdown'
        )
        
        # Fetch and format data from API
        result = await fetch_and_format_data(user_input, input_type)
        
        # Delete processing message
        try:
            await context.bot.delete_message(
                chat_id=update.message.chat_id,
                message_id=processing_msg.message_id
            )
        except:
            pass
        
        # Send the formatted result
        await send_long_message(update, result)
        
    except Exception as e:
        logger.error(f"Error in handle_message: {str(e)}")
        await update.message.reply_text(
            f"❌ *Error Processing Request*\n\nAn error occurred. Please try again.",
            parse_mode='Markdown'
        )

# Helper function to send long messages
async def send_long_message(update: Update, text: str):
    """Split and send long messages properly."""
    try:
        # Telegram message limit is 4096 characters
        if len(text) <= 4096:
            await update.message.reply_text(text, parse_mode='Markdown')
            return
        
        # Split into chunks
        chunks = []
        current_chunk = ""
        
        # Split by lines to maintain readability
        lines = text.split('\n')
        
        for line in lines:
            if len(current_chunk) + len(line) + 1 < 4000:
                current_chunk += line + '\n'
            else:
                chunks.append(current_chunk)
                current_chunk = line + '\n'
        
        if current_chunk:
            chunks.append(current_chunk)
        
        # Send chunks
        for i, chunk in enumerate(chunks):
            if i == 0:
                await update.message.reply_text(chunk, parse_mode='Markdown')
            else:
                header = f"*📄 Continued... (Part {i+1}/{len(chunks)})*\n\n"
                await update.message.reply_text(header + chunk, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in send_long_message: {str(e)}")
        # Try sending without markdown if markdown fails
        try:
            await update.message.reply_text(text[:4000])
        except:
            pass

# Help command
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send help message."""
    help_text = """
🤖 *INFORMATION BOT - HELP*
────────────────────────

*Available Commands:*
/start - Start the bot and see options
/help - Show this help message

*How to Use:*
1. Send any of the following directly:
   • 10-digit Mobile Number (e.g., 6395954711)
   • Vehicle Number (e.g., up26r4007)
   • 6-digit PIN Code (e.g., 262124)
   • 12-digit Aadhar Number (e.g., 123412341234)

2. Or use /start to see interactive buttons

*Features:*
✅ Clean, readable format
✅ Fast response
✅ Multiple results shown
✅ Easy to understand information
✅ Handles long PIN code responses

⚠️ *Note:*
• Information is fetched from public APIs
• Accuracy depends on API data
• No personal data is stored
"""
    try:
        await update.message.reply_text(help_text, parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error in help command: {str(e)}")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Log errors."""
    logger.error(f"Update {update} caused error {context.error}")

# Render health check endpoint (for web service)
from flask import Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "🤖 Telegram Information Bot is running!"

@app.route('/health')
def health():
    return "✅ Bot is healthy!"

# Main function for Render deployment
def main():
    """Start the bot for Render deployment."""
    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add error handler
    application.add_error_handler(error_handler)
    
    # Start the bot
    logger.info("🤖 Information Bot Starting...")
    logger.info("✅ All APIs configured and ready!")
    logger.info("📱 Mobile API: Working")
    logger.info("🚗 Vehicle API: Working")
    logger.info("📬 PIN Code API: Working")
    logger.info("🆔 Aadhar API: Working")
    
    # Start Flask app for health checks
    from threading import Thread
    def run_flask():
        app.run(host='0.0.0.0', port=5000)
    
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()
    
    # Start polling
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
        timeout=30,
        connect_timeout=30
    )

if __name__ == '__main__':
    main()
