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
INFO_CHANNEL_ID = 1361046702404145193  # Channel where info message with buttons will be displayed

# Define role IDs
PLAYER_ROLE_ID = 1376274807284301824  # "Игрок" role ID 

# Define intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Добавляем интент для работы с участниками сервера

# Create bot client
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

# View с кнопками для информационного канала
class InfoView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="🌐 Сайт", style=discord.ButtonStyle.link, url="https://site20-production.up.railway.app/")
    async def website_button(self, interaction: discord.Interaction, button: Button):
        # Кнопка с URL автоматически перенаправляет на сайт
        pass
    
    @discord.ui.button(label="🎮 Как зайти", style=discord.ButtonStyle.primary, custom_id="how_to_join")
    async def how_to_join_button(self, interaction: discord.Interaction, button: Button):
        # Создаем красивый embed для инструкции
        embed = discord.Embed(
            title="🎮 Как подключиться к серверу",
            description="Следуйте этим простым шагам для подключения:",
            color=0x00ff00
        )
        embed.add_field(
            name="📋 Пошаговая инструкция:",
            value="```\n1. Запустите Minecraft версии 1.21+\n2. Перейдите в раздел 'Сетевая игра'\n3. Нажмите 'Добавить сервер'\n4. Введите IP: minestoryvanilla.imba.land\n5. Нажмите 'Готово' и подключитесь```",
            inline=False
        )
        embed.add_field(
            name="⚡ IP адрес сервера:",
            value="`minestoryvanilla.imba.land`",
            inline=True
        )
        embed.add_field(
            name="🔧 Версия:",
            value="`1.21+`",
            inline=True
        )
        embed.set_footer(text="Удачной игры! 🎉")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"Пользователь {interaction.user.name} нажал на кнопку 'Как зайти'")
    
    @discord.ui.button(label="📋 Правила", style=discord.ButtonStyle.secondary, custom_id="rules")
    async def rules_button(self, interaction: discord.Interaction, button: Button):
        # Создаем embed с правилами сервера
        embed = discord.Embed(
            title="📋 Правила сервера MineStory",
            description="Соблюдение правил обязательно для всех игроков!",
            color=0xffaa00
        )
        embed.add_field(
            name="🚫 Запрещено:",
            value="• Гриферство и разрушение чужих построек\n• Использование читов и модификаций\n• Оскорбления и токсичное поведение\n• Спам в чате\n• Кража предметов у других игроков",
            inline=False
        )
        embed.add_field(
            name="✅ Разрешено:",
            value="• Строительство и творчество\n• Торговля между игроками\n• Совместные проекты\n• Помощь новичкам",
            inline=False
        )
        embed.set_footer(text="За нарушение правил предусмотрены санкции! ⚠️")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"Пользователь {interaction.user.name} нажал на кнопку 'Правила'")
    
    @discord.ui.button(label="ℹ️ О сервере", style=discord.ButtonStyle.secondary, custom_id="about_server")
    async def about_server_button(self, interaction: discord.Interaction, button: Button):
        # Создаем embed с информацией о сервере
        embed = discord.Embed(
            title="ℹ️ О сервере MineStory",
            description="Узнайте больше о нашем сервере!",
            color=0x0099ff
        )
        embed.add_field(
            name="🎯 Тип сервера:",
            value="Приватный ванильный сервер",
            inline=True
        )
        embed.add_field(
            name="👥 Сообщество:",
            value="Дружелюбное и активное",
            inline=True
        )
        embed.add_field(
            name="🔧 Плагины:",
            value="• ViaVersion - поддержка разных версий\n• PlasmoVoice - голосовой чат",
            inline=False
        )
        embed.add_field(
            name="🎮 Особенности:",
            value="• Ванильный геймплей\n• Стабильная работа 24/7\n• Регулярные обновления\n• Активная администрация",
            inline=False
        )
        embed.set_footer(text="Присоединяйтесь к нашему сообществу! 🎉")
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        logger.info(f"Пользователь {interaction.user.name} нажал на кнопку 'О сервере'")

# Function to send or update info message
async def send_or_update_info_message(channel):
    if not channel:
        logger.error(f"Error: Info channel with ID {INFO_CHANNEL_ID} not found")
        return False
    
    # Создаем красивый embed для информационного сообщения
    embed = discord.Embed(
        title="🎮 MineStory - Ванильный Minecraft Сервер",
        description="Добро пожаловать на наш приватный ванильный сервер! Здесь вы можете расслабиться и насладиться классическим Minecraft опытом.",
        color=0x00ff88
    )
    
    embed.add_field(
        name="🌟 О сервере:",
        value="MineStory - это уютное место для любителей ванильного Minecraft, где каждый игрок может проявить свою креативность и найти новых друзей.",
        inline=False
    )
    
    embed.add_field(
        name="🔧 Версия и плагины:",
        value="**Версия:** `1.21+`\n**Плагины:**\n• ViaVersion - поддержка разных версий\n• PlasmoVoice - голосовой чат",
        inline=True
    )
    
    embed.add_field(
        name="🎯 IP адрес:",
        value="`minestoryvanilla.imba.land`",
        inline=True
    )
    
    embed.add_field(
        name="🎮 Что вас ждет:",
        value="• Дружелюбное сообщество\n• Стабильная работа 24/7\n• Регулярные события\n• Активная администрация\n• Ванильный геймплей",
        inline=False
    )
    
    embed.set_footer(text="Нажмите на кнопки ниже для получения дополнительной информации! 👇")
    embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/1234567890/attachment.png")  # Можно добавить иконку сервера
    
    # Проверяем, есть ли уже сообщение с кнопками
    has_message = False
    try:
        # Проверяем сообщения в канале
        async for message in channel.history(limit=20):
            if message.author.id == client.user.id and len(message.components) > 0:
                # Если нашли сообщение с кнопками, обновляем его
                has_message = True
                view = InfoView()
                
                # Обновляем сообщение с новым embed и кнопками
                await message.edit(embed=embed, view=view)
                logger.info(f"Обновлено существующее информационное сообщение")
                return True
        
        # Если сообщение не найдено, создаем новое
        if not has_message:
            # Отправляем embed с кнопками
            view = InfoView()
            await channel.send(embed=embed, view=view)
            logger.info(f"Отправлено новое информационное сообщение")
            return True
        
    except Exception as e:
        logger.error(f"Ошибка при отправке/обновлении информационного сообщения: {e}")
        return False

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
    
    @discord.ui.button(label="Подать заявку", style=discord.ButtonStyle.primary, custom_id="submit_ticket")
    async def submit_ticket(self, interaction: discord.Interaction, button: Button):
        # Check if user already has the player role
        player_role = interaction.guild.get_role(PLAYER_ROLE_ID)
        if player_role and player_role in interaction.user.roles:
            await interaction.response.send_message("У вас уже есть роль игрока! Вы можете играть на сервере.", ephemeral=True)
            return
        
        # Open the ticket modal
        modal = TicketModal()
        await interaction.response.send_modal(modal)

# Report Modal class
class ReportModal(Modal, title="Жалоба на игрока"):
    reported_player = TextInput(
        label="Ник нарушителя",
        placeholder="Введите ник игрока, на которого жалуетесь",
        required=True,
    )
    
    violation_type = TextInput(
        label="Тип нарушения",
        placeholder="Например: гриф, читы, оскорбления",
        required=True,
    )
    
    description = TextInput(
        label="Описание нарушения",
        placeholder="Подробно опишите что произошло",
        required=True,
        style=discord.TextStyle.paragraph,
    )
    
    evidence = TextInput(
        label="Доказательства (ссылки на скриншоты/видео)",
        placeholder="Вставьте ссылки на доказательства (необязательно)",
        required=False,
        style=discord.TextStyle.paragraph,
    )
    
    def __init__(self):
        super().__init__(title="Жалоба на игрока")
        
    async def on_submit(self, interaction: discord.Interaction):
        # Get the staff channel
        staff_channel = client.get_channel(STAFF_CHANNEL_ID)
        
        # Создаем эмбед для жалобы
        embed = discord.Embed(
            title=f"Жалоба от {interaction.user.display_name}",
            description="Информация о нарушении:",
            color=discord.Color.red()
        )
        
        embed.add_field(name="Нарушитель", value=self.reported_player.value, inline=True)
        embed.add_field(name="Тип нарушения", value=self.violation_type.value, inline=True)
        embed.add_field(name="Описание", value=self.description.value, inline=False)
        
        if self.evidence.value:
            embed.add_field(name="Доказательства", value=self.evidence.value, inline=False)
        
        # Add timestamp and user ID
        embed.set_footer(text=f"ID пользователя: {interaction.user.id} • {discord.utils.format_dt(interaction.created_at)}")
        
        # Send the embed to the staff channel
        if staff_channel:
            await staff_channel.send(content=f"<@{interaction.user.id}> подал жалобу:", embed=embed)
            await interaction.response.send_message("Ваша жалоба отправлена администрации!", ephemeral=True)
        else:
            logger.error(f"Error: Staff channel with ID {STAFF_CHANNEL_ID} not found")
            await interaction.response.send_message("Ошибка: канал администрации не найден.", ephemeral=True)

# Report View class
class ReportView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="Подать жалобу", style=discord.ButtonStyle.danger, custom_id="submit_report")
    async def submit_report(self, interaction: discord.Interaction, button: Button):
        # Open the report modal
        modal = ReportModal()
        await interaction.response.send_modal(modal)

# Bot events
@client.event
async def on_ready():
    logger.info(f"Бот {client.user} запущен и готов к работе!")
    
    # Синхронизируем команды
    try:
        synced = await tree.sync()
        logger.info(f"Команды успешно синхронизированы")
    except Exception as e:
        logger.error(f"Ошибка при синхронизации команд: {e}")
    
    # Получение канала для заявок
    ticket_channel = client.get_channel(TICKET_CHANNEL_ID)
    
    if ticket_channel:
        logger.info(f"Канал для заявок найден: {ticket_channel.name}")
        # Проверяем, есть ли уже сообщение с кнопкой
        has_message = False
        try:
            # Проверяем сообщения в канале
            async for message in ticket_channel.history(limit=20):
                if message.author.id == client.user.id and len(message.components) > 0:
                    # Если нашли сообщение с кнопкой, обновляем его
                    has_message = True
                    view = TicketView()
                    
                    # Обновляем сообщение с новой кнопкой
                    await message.edit(content="Нажмите кнопку ниже, чтобы подать заявку на сервер:", view=view)
                    logger.info(f"Обновлено существующее сообщение с кнопкой")
                    break
            
            # Если сообщение не найдено, создаем новое
            if not has_message:
                # Отправляем сообщение с кнопкой
                view = TicketView()
                await ticket_channel.send("Нажмите кнопку ниже, чтобы подать заявку на сервер:", view=view)
                logger.info(f"Отправлено новое сообщение с кнопкой")
        
        except Exception as e:
            logger.error(f"Ошибка при отправке/обновлении сообщения с кнопкой: {e}")
    else:
        logger.error(f"Error: Ticket channel with ID {TICKET_CHANNEL_ID} not found")
    
    # Получение канала для жалоб
    report_channel = client.get_channel(REPORT_CHANNEL_ID)
    
    if report_channel:
        logger.info(f"Канал для жалоб найден: {report_channel.name}")
        # Проверяем, есть ли уже сообщение с кнопкой
        has_message = False
        try:
            # Проверяем сообщения в канале
            async for message in report_channel.history(limit=20):
                if message.author.id == client.user.id and len(message.components) > 0:
                    # Если нашли сообщение с кнопкой, обновляем его
                    has_message = True
                    view = ReportView()
                    
                    # Обновляем сообщение с новой кнопкой
                    await message.edit(content="Нажмите кнопку ниже, чтобы подать жалобу на игрока:", view=view)
                    logger.info(f"Обновлено существующее сообщение с кнопками для жалоб")
                    break
            
            # Если сообщение не найдено, создаем новое
            if not has_message:
                # Отправляем сообщение с кнопкой
                view = ReportView()
                await report_channel.send("Нажмите кнопку ниже, чтобы подать жалобу на игрока:", view=view)
                logger.info(f"Отправлено новое сообщение с кнопкой для жалоб")
        
        except Exception as e:
            logger.error(f"Ошибка при отправке/обновлении сообщения с кнопкой для жалоб: {e}")
    else:
        logger.error(f"Error: Report channel with ID {REPORT_CHANNEL_ID} not found")
    
    # Получение информационного канала
    info_channel = client.get_channel(INFO_CHANNEL_ID)
    
    if info_channel:
        logger.info(f"Информационный канал найден: {info_channel.name}")
        # Отправляем или обновляем информационное сообщение
        success = await send_or_update_info_message(info_channel)
        if success:
            logger.info("Информационное сообщение успешно отправлено/обновлено при запуске бота")
        else:
            logger.error("Ошибка при отправке/обновлении информационного сообщения при запуске бота")
    else:
        logger.error(f"Error: Info channel with ID {INFO_CHANNEL_ID} not found")

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

# Команда для отправки информационного сообщения с кнопками
@tree.command(name="send_info", description="Отправить информационное сообщение с кнопками")
@app_commands.default_permissions(administrator=True)
async def send_info(interaction: discord.Interaction):
    # Get the info channel
    info_channel = client.get_channel(INFO_CHANNEL_ID)
    
    if info_channel:
        # Отправляем или обновляем информационное сообщение
        success = await send_or_update_info_message(info_channel)
        
        if success:
            await interaction.response.send_message("Информационное сообщение отправлено/обновлено!", ephemeral=True)
        else:
            await interaction.response.send_message("Ошибка при отправке информационного сообщения.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Ошибка: Информационный канал с ID {INFO_CHANNEL_ID} не найден.", ephemeral=True)

# Команда для отправки сообщения с кнопкой заявки
@tree.command(name="send_ticket", description="Отправить сообщение с кнопкой для подачи заявки")
@app_commands.default_permissions(administrator=True)
async def send_ticket(interaction: discord.Interaction):
    view = TicketView()
    await interaction.response.send_message("Нажмите кнопку ниже, чтобы подать заявку на сервер:", view=view)

# Команда для отправки сообщения с кнопкой жалобы
@tree.command(name="send_report", description="Отправить сообщение с кнопкой для подачи жалобы")
@app_commands.default_permissions(administrator=True)
async def send_report(interaction: discord.Interaction):
    view = ReportView()
    await interaction.response.send_message("Нажмите кнопку ниже, чтобы подать жалобу на игрока:", view=view)

# Run the bot
try:
    client.run(TOKEN, reconnect=True, log_handler=None)
except discord.errors.LoginFailure:
    logger.critical("Неправильный токен бота! Пожалуйста, проверьте токен и перезапустите бота.")
except Exception as e:
    logger.critical(f"Критическая ошибка при запуске бота: {e}")
    import traceback
    traceback.print_exc()
