

import os
import discord
from discord.ext import commands

# ==========================================
# CONFIGURAÇÕES
# ==========================================

TOKEN = os.getenv("DISCORD_TOKEN")
LIMITE_FILA = 4

CARGO_RECRUTA = "| 🔰recruta"
CARGO_MEMBRO = "| 🦁 Sentinela"

CANAL_BOAS_VINDAS_ID = 1556464423957299230

CARGOS_RECRUTADORES = [
    1556530332281344082,
    1556441469978411032
]

CATEGORIA_RECRUTAMENTO_ID = 1557959182429454436

EMOJI_SQUAD = discord.PartialEmoji(
    name="squad_ff",
    id=1557929631972327426
)

EMOJI_ENTRAR = discord.PartialEmoji(
    name="squad_ff",
    id=1557943886230454332
)

EMOJI_SENTINELA_URL = (
    "https://cdn.discordapp.com/emojis/"
    "1557941358990200852.png"
)

# Filas temporárias por servidor.
filas = {}


# ==========================================
# INICIALIZAÇÃO
# ==========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


def obter_fila(guild_id):
    if guild_id not in filas:
        filas[guild_id] = []
    return filas[guild_id]


def pode_administrar(interaction):
    """Somente dono do servidor ou administrador."""
    if interaction.guild is None:
        return False

    if interaction.user.id == interaction.guild.owner_id:
        return True

    return (
        isinstance(interaction.user, discord.Member)
        and interaction.user.guild_permissions.administrator
    )


def obter_jogadores_do_canal(canal):
    """Lê os IDs dos jogadores guardados no tópico."""
    if not isinstance(canal, discord.TextChannel):
        return []

    topico = canal.topic or ""

    for parte in topico.split("|"):
        parte = parte.strip()

        if parte.startswith("sentinela_squad:"):
            ids = parte.split(":", 1)[1].strip()
            try:
                return [
                    int(item)
                    for item in ids.split(",")
                    if item.strip()
                ]
            except ValueError:
                return []

    return []


# ==========================================
# EMBED DA FILA
# ==========================================

def criar_embed_fila(guild_id):
    jogadores = obter_fila(guild_id)

    embed = discord.Embed(
        title="𝐆𝐔𝐄𝐑𝐑𝐀 𝐃𝐄 𝐆𝐔𝐈𝐋𝐃𝐀",
        color=discord.Color.gold()
    )

    embed.description = (
        "⚔️ **FORME SEU SQUAD E AMASSE GERAL NA GUERRA!**\n\n"
        f"{EMOJI_SQUAD} **JOGADORES NA FILA**\n"
        f"**{len(jogadores)} / {LIMITE_FILA}**"
    )

    if jogadores:
        lista = "\n".join(
            f"**{numero}.** <@{jogador_id}>"
            for numero, jogador_id in enumerate(
                jogadores, start=1
            )
        )
    else:
        lista = "Ninguém entrou na fila ainda."

    embed.add_field(
        name="📋 QUEM ESTÁ NA FILA",
        value=lista,
        inline=False
    )

    embed.set_footer(
        text="SENTINELA • GUERRA DE GUILDA",
        icon_url=EMOJI_SENTINELA_URL
    )

    return embed


# ==========================================
# CONFIRMAÇÃO PARA FECHAR A SALA
# ==========================================

class ConfirmarFechamento(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=30)

    @discord.ui.button(
        label="CONFIRMAR FECHAMENTO",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="sentinela_confirmar_fechamento"
    )
    async def confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not pode_administrar(interaction):
            await interaction.response.send_message(
                "❌ Somente o dono ou administradores podem fechar a sala.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
            await interaction.response.send_message(
                "Este botão só funciona em um canal de texto.",
                ephemeral=True
            )
            return

        if not obter_jogadores_do_canal(canal):
            await interaction.response.send_message(
                "❌ Este canal não foi reconhecido como sala do squad.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "🔒 Sala encerrada. O canal será apagado."
        )

        try:
            await canal.delete(
                reason=f"Sala encerrada por {interaction.user}"
            )
        except discord.HTTPException:
            print(f"Não consegui apagar o canal {canal.id}.")


# ==========================================
# BOTÕES DA SALA PRIVADA
# ==========================================

class ControleSquadView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="INICIAR PARTIDA",
        emoji="⚔️",
        style=discord.ButtonStyle.success,
        custom_id="sentinela_iniciar_partida"
    )
    async def iniciar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not pode_administrar(interaction):
            await interaction.response.send_message(
                "❌ Somente o dono ou administradores podem iniciar a partida.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
            await interaction.response.send_message(
                "Canal inválido.",
                ephemeral=True
            )
            return

        jogadores = obter_jogadores_do_canal(canal)

        if len(jogadores) != LIMITE_FILA:
            await interaction.response.send_message(
                "❌ Não consegui confirmar os quatro jogadores desta sala.",
                ephemeral=True
            )
            return

        topico = canal.topic or ""

        if "sentinela_partida_iniciada" in topico:
            await interaction.response.send_message(
                "⚠️ Esta partida já foi iniciada.",
                ephemeral=True
            )
            return

        try:
            await canal.edit(
                topic=topico + " | sentinela_partida_iniciada"
            )
        except discord.HTTPException:
            await interaction.response.send_message(
                "❌ Não consegui registrar o início. Confira minhas permissões.",
                ephemeral=True
            )
            return

        mencoes = " ".join(
            f"<@{jogador_id}>" for jogador_id in jogadores
        )

        await interaction.response.send_message(
            f"⚔️ **PARTIDA INICIADA!**\n\n"
            f"Boa sorte, tropa Sentinela!\n{mencoes}\n\n"
            "💛 Preparem-se para a Guerra de Guilda!"
        )

        button.disabled = True

        try:
            await interaction.message.edit(view=self)
        except discord.HTTPException:
            pass

    @discord.ui.button(
        label="FECHAR SALA",
        emoji="🔒",
        style=discord.ButtonStyle.danger,
        custom_id="sentinela_fechar_sala"
    )
    async def fechar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not pode_administrar(interaction):
            await interaction.response.send_message(
                "❌ Somente o dono ou administradores podem fechar a sala.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
            await interaction.response.send_message(
                "Canal inválido.",
                ephemeral=True
            )
            return

        if not obter_jogadores_do_canal(canal):
            await interaction.response.send_message(
                "❌ Este canal não foi reconhecido como sala do squad.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "⚠️ **Tem certeza que deseja fechar esta sala?**",
            view=ConfirmarFechamento(),
            ephemeral=True
        )


# ==========================================
# CRIAÇÃO DA SALA DO SQUAD
# ==========================================

async def criar_canal_squad(guild, jogadores, categoria=None):
    permissoes = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False
        )
    }

    bot_membro = guild.me

    if bot_membro is None:
        raise RuntimeError("Não consegui localizar o bot no servidor.")

    permissoes[bot_membro] = discord.PermissionOverwrite(
        view_channel=True,
        send_messages=True,
        read_message_history=True,
        manage_channels=True,
        manage_messages=True
    )

    for jogador_id in jogadores:
        membro = guild.get_member(jogador_id)

        if membro is not None:
            permissoes[membro] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )

    ids = ",".join(str(jogador_id) for jogador_id in jogadores)

    canal = await guild.create_text_channel(
        name="🔒・squad-sentinela",
        category=categoria,
        overwrites=permissoes,
        topic=(
            "Canal privado da equipe de Guerra de Guilda. "
            f"| sentinela_squad:{ids}"
        ),
        reason="Squad completo da Guerra de Guilda"
    )

    mencoes = " ".join(
        f"<@{jogador_id}>" for jogador_id in jogadores
    )

    embed = discord.Embed(
        title="𝐆𝐔𝐄𝐑𝐑𝐀 𝐃𝐄 𝐆𝐔𝐈𝐋𝐃𝐀",
        description=(
            "🦁 **SQUAD COMPLETO!**\n\n"
            "Salve, tropa! Os quatro jogadores estão reunidos.\n"
            "Organizem a estratégia e preparem-se para a guerra.\n\n"
            f"👥 **Integrantes:**\n{mencoes}"
        ),
        color=discord.Color.gold()
    )

    embed.set_footer(
        text="SENTINELA • GUERRA DE GUILDA",
        icon_url=EMOJI_SENTINELA_URL
    )

    await canal.send(
        embed=embed,
        view=ControleSquadView()
    )

    return canal


# ==========================================
# BOTÕES DA FILA
# ==========================================

class FilaView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="ENTRAR NA FILA",
        emoji=EMOJI_ENTRAR,
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_fila_entrar"
    )
    async def entrar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este botão só funciona dentro do servidor.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        jogadores = obter_fila(guild.id)
        jogador_id = interaction.user.id

        if jogador_id in jogadores:
            await interaction.response.send_message(
                "⚠️ Você já está na fila!",
                ephemeral=True
            )
            return

        if len(jogadores) >= LIMITE_FILA:
            await interaction.response.send_message(
                "❌ A fila já está completa!",
                ephemeral=True
            )
            return

        jogadores.append(jogador_id)

        if len(jogadores) == LIMITE_FILA:
            categoria = None

            if isinstance(interaction.channel, discord.TextChannel):
                categoria = interaction.channel.category

            try:
                await criar_canal_squad(
                    guild,
                    jogadores.copy(),
                    categoria
                )

            except (discord.Forbidden, discord.HTTPException) as erro:
                jogadores.remove(jogador_id)

                await interaction.response.edit_message(
                    embed=criar_embed_fila(guild.id),
                    view=self
                )

                await interaction.followup.send(
                    "❌ Não consegui criar o canal privado. "
                    "Confira as permissões **Gerenciar Canais**, "
                    "**Ver Canais** e **Enviar Mensagens** do bot.",
                    ephemeral=True
                )

                print(f"Erro ao criar sala: {erro}")
                return

            # Libera a fila para a próxima equipe.
            jogadores.clear()

            await interaction.response.edit_message(
                embed=criar_embed_fila(guild.id),
                view=self
            )

            await interaction.followup.send(
                "🏆 **Squad completo!** O canal privado foi criado. "
                "A fila já está disponível para a próxima equipe.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(
            embed=criar_embed_fila(guild.id),
            view=self
        )

    @discord.ui.button(
        label="SAIR DA FILA",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_fila_sair"
    )
    async def sair(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este botão só funciona dentro do servidor.",
                ephemeral=True
            )
            return

        jogadores = obter_fila(interaction.guild.id)
        jogador_id = interaction.user.id

        if jogador_id not in jogadores:
            await interaction.response.send_message(
                "⚠️ Você não está na fila!",
                ephemeral=True
            )
            return

        jogadores.remove(jogador_id)

        await interaction.response.edit_message(
            embed=criar_embed_fila(interaction.guild.id),
            view=self
        )


# ==========================================
# COMANDO PARA CRIAR A FILA
# ==========================================

@bot.command(name="fila")
@commands.guild_only()
async def fila(ctx):
    await ctx.send(
        embed=criar_embed_fila(ctx.guild.id),
        view=FilaView()
    )


# ==========================================
# OUTROS COMANDOS
# ==========================================

@bot.command(name="ping")
async def ping(ctx):
    latencia = round(bot.latency * 1000)
    await ctx.send(
        f"🏓 **Pong!** Sentinela está funcionando.\n"
        f"📡 Latência: **{latencia} ms**"
    )


@bot.command(name="sentinela")
async def sentinela(ctx):
    embed = discord.Embed(
        title="🦁 SENTINELA",
        description=(
            "Bot oficial da Guilda Sentinela!\n\n"
            "⚔️ Guerra de Guilda\n"
            "🔒 Canais privados para os squads\n"
            "🎫 Central de Atendimento\n"
            "💛 Sempre protegendo a Sentinela."
        ),
        color=discord.Color.gold()
    )
    await ctx.send(embed=embed)


@bot.command(name="ajuda")
async def ajuda(ctx):
    embed = discord.Embed(
        title="🦁 CENTRAL DE COMANDOS",
        description="Confira os comandos disponíveis:",
        color=discord.Color.gold()
    )

    embed.add_field(
        name="🏓 Teste",
        value="`!ping` — Testa se o bot está respondendo.",
        inline=False
    )

    embed.add_field(
        name="🦁 Informações",
        value="`!sentinela` — Mostra informações do bot.",
        inline=False
    )

    embed.add_field(
        name="⚔️ Guerra de Guilda",
        value="`!fila` — Publica o painel da fila.",
        inline=False
    )

    embed.add_field(
        name="🔒 Controle de sala",
        value=(
            "Use os botões **INICIAR PARTIDA** e **FECHAR SALA** "
            "no canal privado do squad."
        ),
        inline=False
    )

    embed.add_field(
        name="🎫 Atendimento",
        value="O sistema de tickets ainda precisa ser integrado.",
        inline=False
    )

    await ctx.send(embed=embed)


# ==========================================
# RECRUTAMENTO AUTOMÁTICO
# ==========================================

@bot.event
async def on_member_update(before, after):
    cargos_antes = {cargo.id for cargo in before.roles}
    cargos_depois = {cargo.id for cargo in after.roles}

    cargo_recruta = discord.utils.get(
        after.guild.roles,
        name=CARGO_RECRUTA
    )

    cargo_membro = discord.utils.get(
        after.guild.roles,
        name=CARGO_MEMBRO
    )

    if cargo_recruta is None or cargo_membro is None:
        return

    recebeu_recruta = (
        cargo_recruta.id not in cargos_antes
        and cargo_recruta.id in cargos_depois
    )

    if recebeu_recruta:
        marcador = f"recrutamento_usuario:{after.id}"

        canal_existente = discord.utils.find(
            lambda canal: (
                isinstance(canal, discord.TextChannel)
                and canal.topic
                and marcador in canal.topic
            ),
            after.guild.channels
        )

        if canal_existente is None:
            permissoes = {
                after.guild.default_role:
                    discord.PermissionOverwrite(
                        view_channel=False
                    ),
                after: discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True
                )
            }

            bot_membro = after.guild.me

            if bot_membro is not None:
                permissoes[bot_membro] = (
                    discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        manage_channels=True,
                        manage_messages=True
                    )
                )

            for cargo_id in CARGOS_RECRUTADORES:
                cargo = after.guild.get_role(cargo_id)

                if cargo is not None:
                    permissoes[cargo] = (
                        discord.PermissionOverwrite(
                            view_channel=True,
                            send_messages=True,
                            read_message_history=True,
                            manage_messages=True
                        )
                    )

            categoria = after.guild.get_channel(
                CATEGORIA_RECRUTAMENTO_ID
            )

            if not isinstance(categoria, discord.CategoryChannel):
                categoria = None

            nome_seguro = after.display_name.lower()

            nome_seguro = "".join(
                caractere
                if caractere.isalnum() or caractere in "-_"
                else "-"
                for caractere in nome_seguro
            ).strip("-_")

            if not nome_seguro:
                nome_seguro = f"candidato-{after.id}"

            try:
                canal = await after.guild.create_text_channel(
                    name=f"recruta-{nome_seguro}"[:100],
                    category=categoria,
                    overwrites=permissoes,
                    topic=(
                        "Canal privado de recrutamento "
                        f"| {marcador}"
                    ),
                    reason=f"Recrutamento iniciado para {after}"
                )

                await canal.send(
                    "🦁 **𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 | 𝐑𝐄𝐂𝐑𝐔𝐓𝐀𝐌𝐄𝐍𝐓𝐎**\n\n"
                    f"Salve, {after.mention}! Bem-vindo(a) "
                    "ao seu canal de recrutamento.\n"
                    "A equipe vai conversar com você por aqui. 💛"
                )

            except discord.Forbidden:
                print(
                    f"Sem permissão para criar canal de recrutamento "
                    f"para {after}."
                )

            except discord.HTTPException as erro:
                print(f"Erro no recrutamento: {erro}")

    recebeu_cargo_membro = (
        cargo_membro.id not in cargos_antes
        and cargo_membro.id in cargos_depois
    )

    if recebeu_cargo_membro and CANAL_BOAS_VINDAS_ID:
        canal_boas_vindas = after.guild.get_channel(
            CANAL_BOAS_VINDAS_ID
        )

        if isinstance(canal_boas_vindas, discord.TextChannel):
            try:
                await canal_boas_vindas.send(
                    "🦁💛 **𝐔𝐌 𝐍𝐎𝐕𝐎 𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 𝐂𝐇𝐄𝐆𝐎𝐔!**\n\n"
                    f"Vamos dar as boas-vindas a {after.mention}, "
                    "o mais novo membro da família **𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀**! ⚔️"
                )
            except discord.Forbidden:
                print("Sem permissão para enviar boas-vindas.")
            except discord.HTTPException as erro:
                print(f"Erro nas boas-vindas: {erro}")


# ==========================================
# EVENTO DE INICIALIZAÇÃO
# ==========================================

@bot.event
async def setup_hook():
    # Registra as views persistentes para os botões continuarem
    # funcionando depois de um reinício, enquanto o bot estiver ativo.
    bot.add_view(FilaView())
    bot.add_view(ControleSquadView())


@bot.event
async def on_ready():
    print("=" * 40)
    print("🦁 SENTINELA BOT ONLINE")
    print(f"Conectado como: {bot.user}")
    print(f"ID: {bot.user.id}")
    print("=" * 40)
    print("Use !fila para criar o painel da guerra.")


# ==========================================
# EXECUÇÃO
# ==========================================

if not TOKEN:
    raise RuntimeError(
        "Token não encontrado! Configure DISCORD_TOKEN nas "
        "variáveis do Railway."
    )

bot.run(TOKEN)
