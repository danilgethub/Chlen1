import discord
from discord import app_commands
from discord.ui import Button, View, Modal, TextInput
import asyncio
import os
import logging

# Настройка логгирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('ticket_bot')

# Получаем токен напрямую из переменной окружения
TOKEN = os.getenv("TOKEN")

if not TOKEN:
    logger.error("ОШИБКА: Токен бота не указан в переменных окружения!")
    logger.error("Добавьте переменную TOKEN в настройках платформы Railway")
    exit(1)

# Define channel IDs
TICKET_CHANNEL_ID = 1359611434862120960  # Channel where ticket button will be displayed
STAFF_CHANNEL_ID = 1362471645922463794   # Channel where completed tickets will be sent
REPORT_CHANNEL_ID = 1362794547012436158  # Channel where report button will be displayed
APPROVED_CHANNEL_ID = 1365696815403630726  # Channel where approved applications will be sent

# Define role IDs
PLAYER_ROLE_ID = 1359775270843842653  # "Игрок" role ID 

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Добавляем интент для работы с участниками сервера

# Create bot client
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# Button View class для кнопок "Принять" и "Отклонить"
class ApplicationActionView(View):
    def __init__(self, applicant_id, applicant_nickname, applicant_age):
        super().__init__(timeout=None)
        self.applicant_id = applicant_id
        self.applicant_nickname = applicant_nickname
        self.applicant_age = applicant_age
    
    @discord.ui.button(label="Принять", style=discord.ButtonStyle.success, custom_id="accept_application")
    async def accept_application_button(self, interaction: discord.Interaction, button: Button):
        # Проверяем, имеет ли пользователь права администратора
        is_admin = interaction.user.guild_permissions.administrator
        
        if not is_admin:
            await interaction.response.send_message("Только администраторы могут принимать заявки.", ephemeral=True)
            return
        
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Получаем сервер и пользователя
            guild = interaction.guild
            applicant = await guild.fetch_member(self.applicant_id)
            
            if not applicant:
                await interaction.followup.send(f"Ошибка: Пользователь не найден на сервере.", ephemeral=True)
                return
            
            # Выдаем роль "Игрок"
            player_role = guild.get_role(PLAYER_ROLE_ID)
            if player_role:
                await applicant.add_roles(player_role, reason="Заявка одобрена администратором")
                
                # Отправляем сообщение в канал одобренных заявок
                approved_channel = client.get_channel(APPROVED_CHANNEL_ID)
                if approved_channel:
                    approved_embed = discord.Embed(
                        title="Новый игрок одобрен",
                        color=discord.Color.green()
                    )
                    approved_embed.add_field(name="Ник в Minecraft", value=self.applicant_nickname, inline=True)
                    approved_embed.add_field(name="Возраст", value=self.applicant_age, inline=True)
                    approved_embed.set_footer(text=f"Заявка одобрена {interaction.user.display_name}")
                    
                    await approved_channel.send(content=f"Заявка от <@{self.applicant_id}> принята:", embed=approved_embed)
                
                # Отправляем сообщение пользователю в личку
                try:
                    server_ip = "minestoryvanilla.imba.land"
                    await applicant.send(f"Ваша заявка на сервер была одобрена администратором! Добро пожаловать!\n\nIP сервера: **{server_ip}**\nДобро пожаловать в наше сообщество!")
                except discord.Forbidden:
                    await interaction.followup.send("Заявка одобрена, но не удалось отправить личное сообщение пользователю.", ephemeral=True)
                
                # Обновляем сообщение с заявкой
                await interaction.message.edit(content=f"{interaction.message.content}\n\n**Заявка ОДОБРЕНА администратором {interaction.user.mention}**", view=None)
                
                await interaction.followup.send(f"Заявка пользователя {applicant.mention} успешно одобрена.", ephemeral=True)
            else:
                await interaction.followup.send(f"Ошибка: Роль игрока не найдена.", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"Произошла ошибка при обработке заявки: {e}", ephemeral=True)
    
    @discord.ui.button(label="Отклонить", style=discord.ButtonStyle.danger, custom_id="reject_application")
    async def reject_application_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        
        try:
            # Получаем пользователя
            guild = interaction.guild
            applicant = await guild.fetch_member(self.applicant_id)
            
            if applicant:
                # Отправляем сообщение пользователю в личку
                try:
                    await applicant.send("Ваша заявка на сервер была отклонена. Вы можете попробовать подать заявку повторно через некоторое время.")
                except discord.Forbidden:
                    await interaction.followup.send("Заявка отклонена, но не удалось отправить личное сообщение пользователю.", ephemeral=True)
            
            # Обновляем сообщение с заявкой
            await interaction.message.edit(content=f"{interaction.message.content}\n\n**Заявка ОТКЛОНЕНА администратором {interaction.user.mention}**", view=None)
            
            await interaction.followup.send("Заявка успешно отклонена.", ephemeral=True)
        
        except Exception as e:
            await interaction.followup.send(f"Произошла ошибка при отклонении заявки: {e}", ephemeral=True)

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
                # Увеличиваем таймаут до 10 минут для большего комфорта пользователей
                griefing_response = await client.wait_for(
                    'message',
                    check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel),
                    timeout=600.0
                )
                embed.add_field(name="Отношение к грифу", value=griefing_response.content, inline=False)
                logger.info(f"Пользователь {user.name} ответил на первый вопрос: {griefing_response.content}")
            except asyncio.TimeoutError:
                embed.add_field(name="Отношение к грифу", value="Не ответил в течение 10 минут", inline=False)
                await user.send("Время ожидания истекло. Ваша заявка отклонена. Повторите попытку и ответьте на все вопросы.")
                logger.warning(f"Таймаут ожидания ответа на первый вопрос от {user.name}")
                return  # Завершаем функцию, не выдаем роль
            except Exception as e:
                logger.error(f"Ошибка при получении ответа на вопрос о грифе: {e}")
                embed.add_field(name="Отношение к грифу", value=f"Ошибка: {e}", inline=False)
                await user.send("Произошла ошибка при обработке вашего ответа. Пожалуйста, попробуйте еще раз.")
                return
            
            # Небольшая задержка между вопросами
            await asyncio.sleep(1)
            
            # Ask about how they found the server
            await user.send("Откуда узнали о сервере?")
            try:
                # Увеличиваем таймаут до 10 минут
                source_response = await client.wait_for(
                    'message',
                    check=lambda m: m.author == user and isinstance(m.channel, discord.DMChannel),
                    timeout=600.0
                )
                embed.add_field(name="Источник информации о сервере", value=source_response.content, inline=False)
                logger.info(f"Пользователь {user.name} ответил на второй вопрос: {source_response.content}")
            except asyncio.TimeoutError:
                embed.add_field(name="Источник информации о сервере", value="Не ответил в течение 10 минут", inline=False)
                await user.send("Время ожидания истекло. Ваша заявка отклонена. Повторите попытку и ответьте на все вопросы.")
                logger.warning(f"Таймаут ожидания ответа на второй вопрос от {user.name}")
                return  # Завершаем функцию, не выдаем роль
            except Exception as e:
                logger.error(f"Ошибка при получении ответа на вопрос об источнике: {e}")
                embed.add_field(name="Источник информации о сервере", value=f"Ошибка: {e}", inline=False)
                await user.send("Произошла ошибка при обработке вашего ответа. Пожалуйста, попробуйте еще раз.")
                return
            
            # Thank the user
            try:
                await user.send("Спасибо за ваши ответы! Ваша заявка полностью отправлена администрации.")
                logger.info(f"Отправлено благодарственное сообщение пользователю {user.name}")
                dm_completed = True
                logger.info(f"Установлен флаг dm_completed = True для {user.name}")
            except Exception as e:
                logger.error(f"Ошибка при отправке благодарственного сообщения: {e}")
                # Даже если не удалось отправить благодарственное сообщение, продолжаем обработку
                dm_completed = True
                logger.warning(f"Установлен флаг dm_completed = True для {user.name} несмотря на ошибку")
        
        except discord.Forbidden:
            # Cannot send DM to the user
            try:
                await interaction.followup.send("Не удалось отправить вам личное сообщение. Пожалуйста, откройте личные сообщения в настройках приватности Discord и попробуйте снова.", ephemeral=True)
                logger.warning(f"Не удалось отправить DM пользователю {user.name} - сообщения закрыты")
            except Exception as e:
                logger.error(f"Ошибка при отправке сообщения о закрытых DM: {e}")
            return  # Завершаем функцию, не выдаем роль
        except Exception as e:
            # Other errors
            logger.error(f"Ошибка при отправке DM: {e}")
            try:
                await interaction.followup.send("Произошла ошибка при обработке заявки. Пожалуйста, попробуйте позже.", ephemeral=True)
            except Exception as follow_up_error:
                logger.error(f"Ошибка при отправке сообщения об ошибке: {follow_up_error}")
            return  # Завершаем функцию, не выдаем роль
            
        # ТОЛЬКО если прошли все проверки ЛС, отправляем заявку администраторам
        if dm_completed:
            logger.info(f"Начинаем процесс отправки заявки для {user.name}")
            success_message = "Ваша заявка успешно отправлена администрации!"
            
            try:
                await interaction.followup.send(success_message, ephemeral=True)
                logger.info(f"Отправлено уведомление об успешной подаче заявки для {user.name}")
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления об успешной подаче заявки: {e}")
            
            # Add timestamp and user ID
            embed.set_footer(text=f"ID пользователя: {interaction.user.id} • {discord.utils.format_dt(interaction.created_at)}")
            
            # Send the embed to the staff channel with buttons
            if staff_channel:
                try:
                    view = ApplicationActionView(interaction.user.id, self.nickname.value, self.age.value)
                    await staff_channel.send(content=f"<@{interaction.user.id}> подал заявку:", embed=embed, view=view)
                    logger.info(f"Заявка для {user.name} успешно отправлена в канал администрации")
                except Exception as e:
                    logger.error(f"Ошибка при отправке заявки в канал администрации: {e}")
                    try:
                        await user.send("Произошла ошибка при отправке вашей заявки администрации. Пожалуйста, свяжитесь с администратором сервера.")
                    except:
                        pass
            else:
                logger.error(f"Error: Staff channel with ID {STAFF_CHANNEL_ID} not found")
                try:
                    await user.send("Не удалось отправить заявку из-за ошибки конфигурации. Пожалуйста, свяжитесь с администратором сервера.")
                except:
                    pass
        else:
            logger.warning(f"Пользователь {user.name} не завершил процесс подачи заявки (dm_completed = False)")
            try:
                await interaction.followup.send("Ваша заявка не была отправлена из-за проблем с личными сообщениями.", ephemeral=True)
            except:
                pass

# Button View class
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.primary, custom_id="ticket_button")
    async def ticket_button(self, interaction: discord.Interaction, button: Button):
        try:
            # Send the modal to the user
            await interaction.response.send_modal(TicketModal())
            logger.info(f"Пользователь {interaction.user.name} нажал на кнопку 'Подать заявку'")
        except Exception as e:
            logger.error(f"Ошибка при отправке модального окна: {e}")
            try:
                await interaction.response.send_message("Произошла ошибка при открытии формы. Пожалуйста, попробуйте еще раз или сообщите администратору.", ephemeral=True)
            except Exception as follow_up_error:
                logger.error(f"Ошибка при отправке сообщения об ошибке: {follow_up_error}")

# View с кнопками для выбора типа жалобы
class ReportTypeView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Жалоба на игрока", style=discord.ButtonStyle.danger, custom_id="report_player")
    async def report_player_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        await create_ticket_channel(interaction, "player")
    
    @discord.ui.button(label="Жалоба о баге", style=discord.ButtonStyle.primary, custom_id="report_bug")
    async def report_bug_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        await create_ticket_channel(interaction, "bug")
    
    @discord.ui.button(label="Жалоба о проблеме", style=discord.ButtonStyle.secondary, custom_id="report_issue")
    async def report_issue_button(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer(ephemeral=True)
        await create_ticket_channel(interaction, "issue")

# Создание приватного канала для тикета
async def create_ticket_channel(interaction: discord.Interaction, ticket_type):
    user = interaction.user
    guild = interaction.guild
    
    if not guild:
        await interaction.followup.send("Ошибка: не удалось получить информацию о сервере", ephemeral=True)
        return
    
    # Определение названия канала
    channel_name = f"тикет-{ticket_type}-{user.name}"
    logger.info(f"Создание тикета {channel_name} для пользователя {user.name}")
    
    try:
        # Получение роли администратора
        admin_roles = [role for role in guild.roles if role.permissions.administrator]
        
        # Создание прав доступа (overwrites)
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
            user: discord.PermissionOverwrite(read_messages=True, send_messages=True)
        }
        
        # Добавление прав для админов
        for role in admin_roles:
            overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True)
        
        # Создание категории "Тикеты" если её нет
        ticket_category = None
        for category in guild.categories:
            if category.name == "Тикеты":
                ticket_category = category
                break
        
        if not ticket_category:
            ticket_category = await guild.create_category("Тикеты")
        
        # Создание текстового канала
        ticket_channel = await guild.create_text_channel(
            name=channel_name,
            overwrites=overwrites,
            category=ticket_category
        )
        
        # Отправка сообщения в новый канал с шаблоном жалобы
        if ticket_type == "player":
            template = """**Жалоба на игрока**

Пожалуйста, заполните следующую информацию:

**Ник игрока:** 
**Ваш ник:** 
**Правило, которое нарушил:** 
**Описание ситуации:** 
**Демонстрация (скриншоты/видео):** 

После заполнения жалобы, ожидайте ответа администрации."""
        
        elif ticket_type == "bug":
            template = """**Жалоба о баге**

Пожалуйста, заполните следующую информацию:

**Ваш ник:** 
**Описание проблемы/бага:** 
**Демонстрация (скриншоты/видео):** 

После заполнения жалобы, ожидайте ответа администрации."""
        
        else:  # issue
            template = """**Жалоба о проблеме**

Пожалуйста, заполните следующую информацию:

**Ваш ник:** 
**Описание проблемы:** 

После заполнения жалобы, ожидайте ответа администрации."""
        
        # Отправка сообщения с шаблоном
        await ticket_channel.send(f"{user.mention}, ваш тикет создан! Пожалуйста, заполните информацию ниже:")
        await ticket_channel.send(template)
        
        # Кнопка для закрытия тикета
        close_view = CloseTicketView()
        await ticket_channel.send("Когда вопрос будет решен, тикет можно закрыть:", view=close_view)
        
        # Ответ пользователю
        await interaction.followup.send(f"Тикет создан! Перейдите в канал {ticket_channel.mention}", ephemeral=True)
        logger.info(f"Тикет {channel_name} успешно создан")
        
    except Exception as e:
        logger.error(f"Ошибка при создании тикета: {e}")
        await interaction.followup.send(f"Произошла ошибка при создании тикета: {e}", ephemeral=True)

# View с кнопкой для закрытия тикета
class CloseTicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.danger, custom_id="close_ticket")
    async def close_ticket_button(self, interaction: discord.Interaction, button: Button):
        # Проверка, является ли пользователь администратором
        is_admin = interaction.user.guild_permissions.administrator
        
        # Если пользователь не администратор, отправляем сообщение
        if not is_admin:
            await interaction.response.send_message("Только администраторы могут закрывать тикеты.", ephemeral=True)
            return
        
        await interaction.response.defer()
        
        # Отправка сообщения перед закрытием
        await interaction.channel.send("Тикет закрывается...")
        logger.info(f"Закрытие тикета {interaction.channel.name} администратором {interaction.user.name}")
        
        # Задержка для чтения сообщения
        await asyncio.sleep(3)
        
        # Удаление канала
        try:
            await interaction.channel.delete()
            logger.info(f"Тикет {interaction.channel.name} успешно закрыт")
        except Exception as e:
            logger.error(f"Ошибка при удалении канала тикета: {e}")
            await interaction.channel.send(f"Ошибка при закрытии тикета: {e}")

# Bot ready event
@client.event
async def on_ready():
    logger.info(f'Бот {client.user} запущен и готов к работе!')
    
    # Sync commands
    try:
        await tree.sync()
        logger.info("Команды успешно синхронизированы")
    except Exception as e:
        logger.error(f"Ошибка при синхронизации команд: {e}")
    
    # Get the ticket channel
    ticket_channel = client.get_channel(TICKET_CHANNEL_ID)
    
    if ticket_channel:
        logger.info(f"Канал для заявок найден: {ticket_channel.name}")
        # Проверяем, есть ли уже сообщение с кнопкой от этого бота
        has_message = False
        try:
            # Проверяем больше сообщений, чтобы точно найти существующее
            async for message in ticket_channel.history(limit=20):
                if message.author.id == client.user.id and len(message.components) > 0:
                    # Проверка работоспособности кнопки - если она интерактивная, оставляем
                    has_message = True
                    view = TicketView()
                    message = await message.edit(view=view)
                    logger.info(f"Обновлено существующее сообщение с кнопкой")
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
                logger.info(f"Отправлено новое сообщение с кнопкой в канал {TICKET_CHANNEL_ID}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения с кнопкой: {e}")
            # Не создаем новое сообщение при ошибке во избежание дублей
            logger.info(f"Пропущено создание нового сообщения для предотвращения дублирования")
    else:
        logger.error(f"Error: Ticket channel with ID {TICKET_CHANNEL_ID} not found")
    
    # Получение канала для жалоб
    report_channel = client.get_channel(REPORT_CHANNEL_ID)
    
    if report_channel:
        logger.info(f"Канал для жалоб найден: {report_channel.name}")
        # Проверяем, есть ли уже сообщение с кнопками жалоб от этого бота
        has_report_message = False
        try:
            # Проверяем сообщения в канале
            async for message in report_channel.history(limit=20):
                if message.author.id == client.user.id and len(message.components) > 0:
                    # Проверка работоспособности кнопок - если они интерактивные, оставляем
                    has_report_message = True
                    view = ReportTypeView()
                    message = await message.edit(view=view)
                    logger.info(f"Обновлено существующее сообщение с кнопками для жалоб")
                    break
            
            # Если нет рабочего сообщения с кнопками, создаем новое
            if not has_report_message:
                # Create an embed for the report message
                embed = discord.Embed(
                    title="Система жалоб",
                    description="Нажмите на одну из кнопок ниже, чтобы создать тикет с жалобой.",
                    color=discord.Color.red()
                )
                
                # Create a view with the report buttons
                view = ReportTypeView()
                
                # Send the embed with the view
                await report_channel.send(embed=embed, view=view)
                logger.info(f"Отправлено новое сообщение с кнопками жалоб в канал {REPORT_CHANNEL_ID}")
        except Exception as e:
            logger.error(f"Ошибка при обновлении сообщения с кнопками жалоб: {e}")
            logger.info(f"Пропущено создание нового сообщения для предотвращения дублирования")
    else:
        logger.error(f"Error: Report channel with ID {REPORT_CHANNEL_ID} not found")

# Добавляем обработчики для мониторинга соединения
@client.event
async def on_connect():
    logger.info("Бот подключился к Discord")

@client.event
async def on_disconnect():
    logger.warning("Бот отключился от Discord. Ожидание переподключения...")

@client.event
async def on_resumed():
    logger.info("Сессия успешно восстановлена")

@client.event
async def on_error(event, *args, **kwargs):
    logger.error(f"Произошла ошибка в событии {event}: {args}, {kwargs}")
    import traceback
    traceback.print_exc()

@client.event 
async def on_application_command_error(interaction, error):
    logger.error(f"Ошибка при выполнении команды: {error}")
    import traceback
    traceback.print_exc()
    try:
        await interaction.response.send_message(f"Произошла ошибка: {error}", ephemeral=True)
    except discord.errors.InteractionResponded:
        await interaction.followup.send(f"Произошла ошибка: {error}", ephemeral=True)
    except Exception as e:
        logger.error(f"Не удалось отправить сообщение об ошибке: {e}")

# Команда для отправки сообщения с кнопками жалоб
@tree.command(name="send_report_buttons", description="Отправить сообщение с кнопками для создания жалоб")
@app_commands.default_permissions(administrator=True)
async def send_report_buttons(interaction: discord.Interaction):
    # Get the report channel
    report_channel = client.get_channel(REPORT_CHANNEL_ID)
    
    if report_channel:
        # Проверяем, есть ли уже сообщение с кнопками
        has_message = False
        try:
            # Проверяем сообщения в канале
            async for message in report_channel.history(limit=20):
                if message.author.id == client.user.id and len(message.components) > 0:
                    # Если нашли сообщение с кнопками, обновляем его
                    has_message = True
                    view = ReportTypeView()
                    await message.edit(view=view, embed=message.embeds[0] if message.embeds else None)
                    await interaction.response.send_message("Существующее сообщение с кнопками жалоб обновлено!", ephemeral=True)
                    break
            
            # Если сообщение не найдено, создаем новое
            if not has_message:
                # Create an embed for the report message
                embed = discord.Embed(
                    title="Система жалоб",
                    description="Нажмите на одну из кнопок ниже, чтобы создать тикет с жалобой.",
                    color=discord.Color.red()
                )
                
                # Create a view with the report buttons
                view = ReportTypeView()
                
                # Send the embed with the view
                await report_channel.send(embed=embed, view=view)
                await interaction.response.send_message("Новое сообщение с кнопками жалоб отправлено!", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения с кнопками жалоб: {e}")
            await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)
    else:
        # Respond with an error
        await interaction.response.send_message(f"Ошибка: канал с ID {REPORT_CHANNEL_ID} не найден", ephemeral=True)

# Command to send a new ticket message - для заявок на вступление на сервер
@tree.command(name="send_ticket", description="Отправить сообщение с кнопкой заявки на вступление")
@app_commands.default_permissions(administrator=True)
async def send_ticket(interaction: discord.Interaction):
    # Get the ticket channel
    ticket_channel = client.get_channel(TICKET_CHANNEL_ID)
    
    if ticket_channel:
        # Проверяем, есть ли уже сообщение с кнопкой
        has_message = False
        try:
            # Проверяем сообщения в канале
            async for message in ticket_channel.history(limit=20):
                if message.author.id == client.user.id and len(message.components) > 0:
                    # Если нашли сообщение с кнопкой, обновляем его
                    has_message = True
                    view = TicketView()
                    await message.edit(view=view, embed=message.embeds[0] if message.embeds else None)
                    await interaction.response.send_message("Существующее сообщение с кнопкой обновлено!", ephemeral=True)
                    break
            
            # Если сообщение не найдено, создаем новое
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
                await interaction.response.send_message("Новое сообщение с кнопкой заявки отправлено!", ephemeral=True)
            
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения с кнопкой: {e}")
            await interaction.response.send_message(f"Произошла ошибка: {e}", ephemeral=True)
    else:
        # Respond with an error
        await interaction.response.send_message(f"Ошибка: канал с ID {TICKET_CHANNEL_ID} не найден", ephemeral=True)

# Start the bot
try:
    client.run(TOKEN, reconnect=True, log_handler=None)
except discord.errors.LoginFailure:
    logger.critical("Неправильный токен бота! Пожалуйста, проверьте токен и перезапустите бота.")
except Exception as e:
    logger.critical(f"Критическая ошибка при запуске бота: {e}")
    import traceback
    traceback.print_exc() 
