
import os
import discord
from discord.ext import commands

# ==============================
# CONFIGURAÇÕES
# ==============================

TOKEN = os.getenv("DISCORD_TOKEN")
LIMITE_FILA = 4

# ==============================
# CONFIGURAÇÕES DE RECRUTAMENTO
# ==============================

# Os nomes precisam ser iguais aos cargos/canais do seu Discord.
CARGO_RECRUTA = "| 🔰recruta"
CARGO_MEMBRO = "| 🦁 Sentinela"

# COLOQUE AQUI O ID do canal de boas-vindas que você já criou.
# Para pegar o ID: ative o Modo Desenvolvedor no Discord,
# clique com o botão direito no canal e escolha "Copiar ID".
CANAL_BOAS_VINDAS_ID = 1556464423957299230

# Opcional: IDs dos cargos que também poderão ver os canais de recrutamento.
# Exemplo: CARGOS_RECRUTADORES = [123456789012345678, 987654321098765432]
CARGOS_RECRUTADORES = [1556530332281344082, 1556441469978411032]

# Opcional: ID de uma categoria onde os canais privados serão criados.
# Deixe 0 para criar os canais fora de uma categoria específica.
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

# Guarda as filas e os canais de cada servidor
filas = {}
canais_squad = {}


# ==============================
# INICIALIZAÇÃO DO BOT
# ==============================

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


# ==============================
# EMBED DA GUERRA DE GUILDA
# ==============================

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

    if not jogadores:
        lista = "Ninguém entrou na fila ainda."
    else:
        lista = "\n".join(
            f"**{numero}.** <@{jogador_id}>"
            for numero, jogador_id in enumerate(
                jogadores, start=1
            )
        )

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


# ==============================
# CRIAR CANAL PRIVADO DO SQUAD
# ==============================

async def criar_canal_squad(guild, jogadores, categoria=None):
    permissoes = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False
        ),
        guild.me: discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True
        )
    }

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

    canal = await guild.create_text_channel(
        name="🔒・squad-sentinela",
        category=categoria,
        overwrites=permissoes,
        topic="Canal privado da equipe de Guerra de Guilda da Sentinela."
    )

    mencoes = " ".join(
        f"<@{jogador_id}>" for jogador_id in jogadores
    )

    await canal.send(
        f"⚔️ **SQUAD COMPLETO — GUERRA DE GUILDA!**\n\n"
        f"Salve, equipe Sentinela! Os quatro jogadores estão reunidos.\n\n"
        f"👥 **Integrantes:**\n{mencoes}\n\n"
        f"💛 Organizem a estratégia por aqui!"
    )

    return canal


# ==============================
# BOTÕES DA FILA
# ==============================

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
        guild_id = guild.id
        jogadores = obter_fila(guild_id)
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
        canal_criado = None

        # Quando o quarto jogador entra, cria o canal privado
        if len(jogadores) == LIMITE_FILA:
            try:
                categoria = None

                if isinstance(interaction.channel, discord.TextChannel):
                    categoria = interaction.channel.category

                canal_criado = await criar_canal_squad(
                    guild,
                    jogadores.copy(),
                    categoria
                )

                canais_squad[guild_id] = canal_criado.id

            except discord.Forbidden:
                jogadores.remove(jogador_id)

                await interaction.response.edit_message(
                    embed=criar_embed_fila(guild_id),
                    view=self
                )

                await interaction.followup.send(
                    "❌ Não consegui criar o canal privado. "
                    "Peça à administração para conferir se o bot "
                    "tem a permissão **Gerenciar Canais**.",
                    ephemeral=True
                )
                return

            except discord.HTTPException:
                jogadores.remove(jogador_id)

                await interaction.response.edit_message(
                    embed=criar_embed_fila(guild_id),
                    view=self
                )

                await interaction.followup.send(
                    "❌ O Discord não permitiu criar o canal agora. "
                    "Tente novamente.",
                    ephemeral=True
                )
                return

        await interaction.response.edit_message(
            embed=criar_embed_fila(guild_id),
            view=self
        )

        if canal_criado is not None:
            await interaction.followup.send(
                f"🏆 **Squad completo!** Seu canal privado foi criado: "
                f"{canal_criado.mention}",
                ephemeral=True
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

        guild_id = interaction.guild.id
        jogadores = obter_fila(guild_id)
        jogador_id = interaction.user.id

        if jogador_id not in jogadores:
            await interaction.response.send_message(
                "⚠️ Você não está na fila!",
                ephemeral=True
            )
            return

        jogadores.remove(jogador_id)

        # Se alguém sair de um squad já completo,
        # fecha o canal antigo para não manter uma equipe desatualizada.
        canal_id = canais_squad.pop(guild_id, None)

        if canal_id is not None:
            canal = interaction.guild.get_channel(canal_id)

            if canal is not None:
                try:
                    await canal.delete(
                        reason="Um jogador saiu da fila da Guerra de Guilda."
                    )
                except discord.HTTPException:
                    pass

        await interaction.response.edit_message(
            embed=criar_embed_fila(guild_id),
            view=self
        )


# ==============================
# COMANDO PARA CRIAR A FILA
# ==============================

@bot.command(name="fila")
@commands.guild_only()
async def fila(ctx):
    await ctx.send(
        embed=criar_embed_fila(ctx.guild.id),
        view=FilaView()
    )


# ==============================
# COMANDO PING
# ==============================

@bot.command(name="ping")
async def ping(ctx):
    latencia = round(bot.latency * 1000)

    await ctx.send(
        f"🏓 **Pong!** Sentinela está funcionando.\n"
        f"📡 Latência: **{latencia} ms**"
    )


# ==============================
# COMANDO SENTINELA
# ==============================

@bot.command(name="sentinela")
async def sentinela(ctx):
    embed = discord.Embed(
        title="🦁 SENTINELA",
        description=(
            "Bot oficial da Guilda Sentinela!\n\n"
            "⚔️ Guerra de Guilda\n"
            "🔒 Canal privado automático para o squad\n"
            "🎫 Central de Atendimento\n"
            "💛 Sempre protegendo a Sentinela."
        ),
        color=discord.Color.gold()
    )

    await ctx.send(embed=embed)


# ==============================
# COMANDO AJUDA
# ==============================

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
        value="`!sentinela` — Mostra as informações do bot.",
        inline=False
    )

    embed.add_field(
        name="⚔️ Guerra de Guilda",
        value="`!fila` — Publica o painel da fila.",
        inline=False
    )

    embed.add_field(
        name="🎫 Atendimento",
        value="O sistema de tickets ainda precisa ser adicionado.",
        inline=False
    )

    await ctx.send(embed=embed)


# ==============================
# REGISTRO DOS BOTÕES
# ==============================

bot.add_view(FilaView())


# ==============================
# RECRUTAMENTO AUTOMÁTICO
# ==============================

@bot.event
async def on_member_update(before, after):
    # Só reage quando cargos são adicionados/removidos.
    cargos_antes = {cargo.id for cargo in before.roles}
    cargos_depois = {cargo.id for cargo in after.roles}

    cargo_recruta = discord.utils.get(after.guild.roles, name=CARGO_RECRUTA)
    cargo_membro = discord.utils.get(after.guild.roles, name=CARGO_MEMBRO)

    if cargo_recruta is None or cargo_membro is None:
        return

    # Quando a pessoa recebe o cargo Recruta, cria o canal privado.
    recebeu_recruta = (
        cargo_recruta.id not in cargos_antes
        and cargo_recruta.id in cargos_depois
    )

    if recebeu_recruta:
        # Evita criar outro canal se o evento acontecer novamente.
        marcador = f"recrutamento_usuario:{after.id}"
        canal_existente = discord.utils.find(
            lambda canal: isinstance(canal, discord.TextChannel)
            and canal.topic
            and marcador in canal.topic,
            after.guild.channels
        )

        if canal_existente is None:
            permissoes = {
                after.guild.default_role: discord.PermissionOverwrite(
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

            # Libera acesso ao bot que criou o canal.
            bot_membro = after.guild.me
            if bot_membro is not None:
                permissoes[bot_membro] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    manage_messages=True
                )

            # Libera os cargos de recrutadores configurados acima.
            for cargo_id in CARGOS_RECRUTADORES:
                cargo = after.guild.get_role(cargo_id)
                if cargo is not None:
                    permissoes[cargo] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        manage_messages=True
                    )

            categoria = after.guild.get_channel(CATEGORIA_RECRUTAMENTO_ID)
            if not isinstance(categoria, discord.CategoryChannel):
                categoria = None

            nome_seguro = after.display_name.lower()
            nome_seguro = "".join(
                caractere if caractere.isalnum() or caractere in "-_" else "-"
                for caractere in nome_seguro
            ).strip("-_")
            if not nome_seguro:
                nome_seguro = f"candidato-{after.id}"

            try:
                canal = await after.guild.create_text_channel(
                    name=f"recruta-{nome_seguro}"[:100],
                    category=categoria,
                    overwrites=permissoes,
                    topic=f"Canal privado de recrutamento | {marcador}",
                    reason=f"Recrutamento iniciado para {after}"
                )
                await canal.send(
                    f"🦁 **𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 | 𝐑𝐄𝐂𝐑𝐔𝐓𝐀𝐌𝐄𝐍𝐓𝐎**\n\n"
                    f"Salve, {after.mention}! Bem-vindo(a) ao seu canal de recrutamento.\n"
                    "A equipe vai conversar com você por aqui. 💛"
                )
            except discord.Forbidden:
                print(
                    f"Não consegui criar o canal de recrutamento para {after}. "
                    "Confira se o bot tem Gerenciar Canais e Ver Canais."
                )
            except discord.HTTPException as erro:
                print(f"Erro ao criar canal de recrutamento: {erro}")

    # Quando a pessoa recebe o cargo de membro, envia boas-vindas.
    recebeu_cargo_membro = (
        cargo_membro.id not in cargos_antes
        and cargo_membro.id in cargos_depois
    )

    if recebeu_cargo_membro and CANAL_BOAS_VINDAS_ID:
        canal_boas_vindas = after.guild.get_channel(CANAL_BOAS_VINDAS_ID)

        if isinstance(canal_boas_vindas, discord.TextChannel):
            try:
                await canal_boas_vindas.send(
                    f"🦁💛 **𝐔𝐌 𝐍𝐎𝐕𝐎 𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 𝐂𝐇𝐄𝐆𝐎𝐔!**\n\n"
                    f"Vamos dar as boas-vindas a {after.mention}, "
                    "o mais novo membro da família **𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀**! ⚔️"
                )
            except discord.Forbidden:
                print(
                    "Não consegui enviar a mensagem de boas-vindas. "
                    "Confira se o bot pode ver o canal e enviar mensagens."
                )
            except discord.HTTPException as erro:
                print(f"Erro ao enviar boas-vindas: {erro}")


# ==============================
# INICIALIZAÇÃO
# ==============================

@bot.event
async def on_ready():
    print("=" * 40)
    print("🦁 SENTINELA BOT ONLINE")
    print(f"Conectado como: {bot.user}")
    print(f"ID: {bot.user.id}")
    print("=" * 40)
    print("Use !fila para criar a fila de guerra.")
    print("Recrutamento automático ativo: confira os nomes dos cargos e o ID do canal de boas-vindas.")


if not TOKEN:
    raise RuntimeError(
        "Token não encontrado! Configure DISCORD_TOKEN no terminal."
    )

bot.run(TOKEN)