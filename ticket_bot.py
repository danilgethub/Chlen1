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
intents.members = True  # Добавляем интент для работы с участниками сервера

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
        # Сначала отправляем начальное сообщение
        await interaction.response.send_message("Ваша заявка принята! Проверьте личные сообщения для завершения заявки.", ephemeral=True)
        
        # Get the staff channel
        staff_channel = client.get_channel(STAFF_CHANNEL_ID)
        
        # Создаем эмбед для заявки
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
        
        # Get user for DM
        user = interaction.user
        
        # Флаг успешного прохождения ЛС этапа
        dm_completed = False
        
        # Send an additional DM to get more information
        try:
            # Проверяем возможность отправить DM
            test_dm = await user.send("Пожалуйста, ответьте на дополнительные вопросы (это займет не более минуты). Если вы не ответите, ваша заявка не будет отправлена администрации.")
            
            # Ask about griefing
            griefing_question = await user.send("Как вы относитесь к грифу?")
            try:
                griefing_response = await client.wait_for(
                    'message',
                    check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel),
                    timeout=300.0
                )
                embed.add_field(name="Отношение к грифу", value=griefing_response.content, inline=False)
            except asyncio.TimeoutError:
                embed.add_field(name="Отношение к грифу", value="Не ответил в течение 5 минут", inline=False)
                await user.send("Время ожидания истекло. Ваша заявка отклонена. Повторите попытку и ответьте на все вопросы.")
                return  # Завершаем функцию, не выдаем роль
            
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
                embed.add_field(name="Источник информации о сервере", value="Не ответил в течение 5 минут", inline=False)
                await user.send("Время ожидания истекло. Ваша заявка отклонена. Повторите попытку и ответьте на все вопросы.")
                return  # Завершаем функцию, не выдаем роль
            
            # Thank the user
            await user.send("Спасибо за ваши ответы! Ваша заявка полностью отправлена администрации.")
            dm_completed = True
        
        except discord.Forbidden:
            # Cannot send DM to the user
            try:
                await interaction.followup.send("Не удалось отправить вам личное сообщение. Пожалуйста, откройте личные сообщения в настройках приватности Discord и попробуйте снова.", ephemeral=True)
            except:
                pass
            return  # Завершаем функцию, не выдаем роль
        except Exception as e:
            # Other errors
            print(f"Ошибка при отправке DM: {e}")
            try:
                await interaction.followup.send("Произошла ошибка при обработке заявки. Пожалуйста, попробуйте позже.", ephemeral=True)
            except:
                pass
            return  # Завершаем функцию, не выдаем роль
            
        # ТОЛЬКО если прошли все проверки ЛС, выдаем роль
        if dm_completed:
            success_message = "Ваша заявка успешно отправлена администрации!"
            
            # Выдаем роль пользователю
            try:
                # ID роли для выдачи
                ROLE_ID = 1359775270843842653
                
                # Получаем объект сервера
                guild = interaction.guild
                if guild:
                    # Получаем объект роли
                    role = guild.get_role(ROLE_ID)
                    if role:
                        # Выдаем роль пользователю
                        await interaction.user.add_roles(role, reason="Подал заявку на сервер")
                        print(f"Пользователю {interaction.user.name} выдана роль {role.name}")
                        success_message += f" Вам выдана роль \"{role.name}\"!"
                    else:
                        print(f"Ошибка: Роль с ID {ROLE_ID} не найдена")
                else:
                    print("Ошибка: Не удалось получить объект сервера")
            except Exception as e:
                print(f"Ошибка при выдаче роли: {e}")
            
            try:
                await interaction.followup.send(success_message, ephemeral=True)
            except:
                pass
            
            # Add timestamp and user ID
            embed.set_footer(text=f"ID пользователя: {interaction.user.id} • {discord.utils.format_dt(interaction.created_at)}")
            
            # Send the embed to the staff channel
            if staff_channel:
                await staff_channel.send(content=f"<@{interaction.user.id}> подал заявку:", embed=embed)
            else:
                print(f"Error: Staff channel with ID {STAFF_CHANNEL_ID} not found")

# Button View class
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.primary, custom_id="ticket_button")
    async def ticket_button(self, interaction: discord.Interaction, button: Button):
        try:
            # Send the modal to the user
            await interaction.response.send_modal(TicketModal())
        except Exception as e:
            print(f"Ошибка при отправке модального окна: {e}")
            try:
                await interaction.response.send_message("Произошла ошибка при открытии формы. Пожалуйста, попробуйте еще раз или сообщите администратору.", ephemeral=True)
            except:
                pass

# Bot ready event
@client.event
async def on_ready():
    print(f'Бот {client.user} запущен и готов к работе!')
    
    # Sync commands
    await tree.sync()
    
    # Get the ticket channel
    ticket_channel = client.get_channel(TICKET_CHANNEL_ID)
    
    if ticket_channel:
        # Проверяем, есть ли уже сообщение с кнопкой от этого бота
        has_message = False
        try:
            # Проверяем только последние 5 сообщений для оптимизации
            async for message in ticket_channel.history(limit=5):
                if message.author == client.user and len(message.components) > 0:
                    # Проверка работоспособности кнопки - если она интерактивная, оставляем
                    has_message = True
                    view = TicketView()
                    message = await message.edit(view=view)
                    print(f"Обновлено существующее сообщение с кнопкой")
                    break
            
            # Если нет рабочего сообщения с кнопкой, создаем новое
            if not has_message:
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
                print(f"Отправлено новое сообщение с кнопкой в канал {TICKET_CHANNEL_ID}")
        except Exception as e:
            print(f"Ошибка при обновлении сообщения с кнопкой: {e}")
            # В случае ошибки создаем новое сообщение
            try:
                embed = discord.Embed(
                    title="Заявка на сервер",
                    description="Нажмите на кнопку ниже, чтобы подать заявку на вступление на наш Minecraft сервер!",
                    color=discord.Color.green()
                )
                view = TicketView()
                await ticket_channel.send(embed=embed, view=view)
                print(f"Создано новое сообщение после ошибки")
            except Exception as e2:
                print(f"Критическая ошибка при создании сообщения: {e2}")
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
