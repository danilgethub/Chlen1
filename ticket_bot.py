import discord
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
import asyncio
import os

# Получаем токен напрямую из переменной окружения
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    print("ОШИБКА: Токен бота не указан в переменных окружения!")
    print("Добавьте переменную TOKEN в настройках платформы Railway")
    exit(1)

# Define channel IDs
TICKET_CHANNEL_ID = 1359611434862120960  # Channel where ticket button will be displayed
STAFF_CHANNEL_ID = 1362471645922463794   # Channel where completed tickets will be sent

# Define intents
intents = discord.Intents.default()
intents.message_content = True

# Create bot client
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Ticket Modal class
class TicketModal(Modal, title="Заявка на сервер"):
    nickname = TextInput(
        label="Ник",
        placeholder="Введите ваш игровой ник",
        required=True,
    )
    
    age = TextInput(
        label="Возраст",
        placeholder="Укажите ваш возраст",
        required=True,
    )
    
    experience = TextInput(
        label="Опыт на подобных серверах",
        placeholder="Играли ли вы на подобных серверах?",
        required=True,
    )
    
    adequacy = TextInput(
        label="Оцените свою адекватность от 1 до 10",
        placeholder="Например: 8",
        required=True,
    )
    
    plans = TextInput(
        label="Чем планируете заниматься",
        placeholder="Опишите ваши планы на сервере",
        required=True,
        style=discord.TextStyle.paragraph,
    )
    
    def __init__(self):
        super().__init__(title="Заявка на сервер")
        
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message("Ваша заявка отправлена! Спасибо за интерес к нашему серверу.", ephemeral=True)
        
        # Get the staff channel
        staff_channel = client.get_channel(STAFF_CHANNEL_ID)
        
        if staff_channel:
            # Create an embed for the ticket
            embed = discord.Embed(
                title=f"Новая заявка от {self.nickname.value}",
                description="Информация об игроке:",
                color=discord.Color.blue()
            )
            
            embed.add_field(name="Ник", value=self.nickname.value, inline=False)
            embed.add_field(name="Возраст", value=self.age.value, inline=False)
            embed.add_field(name="Играл на подобных серверах", value=self.experience.value, inline=False)
            embed.add_field(name="Самооценка адекватности", value=self.adequacy.value, inline=False)
            embed.add_field(name="Планы на сервере", value=self.plans.value, inline=False)
            
            # Get the additional questions from the second page
            interaction_message = interaction.message if hasattr(interaction, 'message') else None
            user = interaction.user
            
            # Send an additional DM to get more information
            try:
                await user.send("Пожалуйста, ответьте на дополнительные вопросы:")
                
                # Ask about griefing
                await user.send("Как вы относитесь к грифу?")
                try:
                    griefing_response = await client.wait_for(
                        'message',
                        check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel),
                        timeout=300.0
                    )
                    embed.add_field(name="Отношение к грифу", value=griefing_response.content, inline=False)
                except asyncio.TimeoutError:
                    embed.add_field(name="Отношение к грифу", value="Не ответил", inline=False)
                
                # Ask about how they found the server
                await user.send("Откуда узнали о сервере?")
                try:
                    source_response = await client.wait_for(
                        'message',
                        check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel),
                        timeout=300.0
                    )
                    embed.add_field(name="Источник информации о сервере", value=source_response.content, inline=False)
                except asyncio.TimeoutError:
                    embed.add_field(name="Источник информации о сервере", value="Не ответил", inline=False)
                
                # Thank the user
                await user.send("Спасибо за ваши ответы! Ваша заявка полностью отправлена администрации.")
            
            except discord.Forbidden:
                # Cannot send DM to the user
                embed.add_field(name="Дополнительная информация", value="Не удалось отправить DM пользователю для получения дополнительной информации", inline=False)
            
            # Add timestamp and user ID
            embed.set_footer(text=f"ID пользователя: {interaction.user.id} • {discord.utils.format_dt(interaction.created_at)}")
            
            # Send the embed to the staff channel
            await staff_channel.send(content=f"<@{interaction.user.id}> подал заявку:", embed=embed)
        else:
            # Log an error if the staff channel is not found
            print(f"Error: Staff channel with ID {STAFF_CHANNEL_ID} not found")

# Button View class
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.primary, custom_id="ticket_button")
    async def ticket_button(self, interaction: discord.Interaction, button: Button):
        # Send the modal to the user
        await interaction.response.send_modal(TicketModal())

# Bot ready event
@client.event
async def on_ready():
    print(f'Бот {client.user} запущен и готов к работе!')
    
    # Sync commands
    await tree.sync()
    
    # Get the ticket channel
    ticket_channel = client.get_channel(TICKET_CHANNEL_ID)
    
    if ticket_channel:
        # Check if there's already a ticket message
        async for message in ticket_channel.history(limit=100):
            if message.author == client.user and len(message.components) > 0:
                # A message with components from this bot already exists
                print(f"Ticket message already exists")
                return
        
        # Create an embed for the ticket message
        embed = discord.Embed(
            title="Заявка на сервер",
            description="Нажмите на кнопку ниже, чтобы подать заявку на вступление на наш Minecraft сервер!",
            color=discord.Color.green()
        )
        
        # Create a view with the ticket button
        view = TicketView()
        
        # Send the embed with the view
        await ticket_channel.send(embed=embed, view=view)
        print(f"Sent ticket message to channel {TICKET_CHANNEL_ID}")
    else:
        print(f"Error: Ticket channel with ID {TICKET_CHANNEL_ID} not found")

# Command to send a new ticket message
@tree.command(name="send_ticket", description="Отправить сообщение с кнопкой заявки")
@app_commands.default_permissions(administrator=True)
async def send_ticket(interaction: discord.Interaction):
    # Create an embed for the ticket message
    embed = discord.Embed(
        title="Заявка на сервер",
        description="Нажмите на кнопку ниже, чтобы подать заявку на вступление на наш Minecraft сервер!",
        color=discord.Color.green()
    )
    
    # Create a view with the ticket button
    view = TicketView()
    
    # Respond to the interaction
    await interaction.response.send_message("Отправляю сообщение с кнопкой заявки...", ephemeral=True)
    
    # Get the ticket channel
    ticket_channel = client.get_channel(TICKET_CHANNEL_ID)
    
    if ticket_channel:
        # Send the embed with the view
        await ticket_channel.send(embed=embed, view=view)
    else:
        # Respond with an error
        await interaction.followup.send(f"Ошибка: канал с ID {TICKET_CHANNEL_ID} не найден", ephemeral=True)

# Start the bot
client.run(TOKEN) 
