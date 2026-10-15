import os
import asyncio
import io
import aiohttp
import discord
from discord.ext import commands

# ==========================================
# CONFIGURACOES
# ==========================================

TOKEN = os.getenv("DISCORD_TOKEN")

LIMITE_FILA = 4
TEMPO_EXCLUSAO_CANAL = 5

CARGO_RECRUTA = "| 🔰recruta"
CARGO_MEMBRO = "| 🦁 Sentinela"

CARGO_MODERADOR_ID = 1556530332281344082
CARGO_ADM_ID = 1556441469978411032

CANAL_BOAS_VINDAS_ID = 1556464423957299230
CANAL_REGRAS_ID = 1556521435302989904
CANAL_PASSE_BOOYAAH_ID = 1558596818948984933
CATEGORIA_RECRUTAMENTO_ID = 1557959182429454436

IMAGEM_BOAS_VINDAS = (
    "https://i.pinimg.com/474x/cf/a8/ac/"
    "cfa8acf9d3323076c8f1a4c5071a36c6.jpg"
)

URL_IMAGEM_PASSE = (
    "https://cdn.discordapp.com/attachments/1556840973022011402/"
    "1558630340573143050/"
    "60d5e3bd-6b8f-4d42-abf9-4b020a751464.jpg"
    "?ex=6acc231f&is=6acad19f&hm="
    "3b96e4c4f7630dba394437ac341c1909a360e343183848f028cb00ae4da67b12"
)

# ==========================================
# EMOJIS PERSONALIZADOS
# ==========================================

EMOJI_SQUAD = discord.PartialEmoji(
    name="squad_ff", id=1557929631972327426
)

EMOJI_ENTRAR = discord.PartialEmoji(
    name="ump_roxa", id=1557943886230454332
)

EMOJI_SENTINELA_URL = (
    "https://cdn.discordapp.com/emojis/1557941358990200852.webp"
)

EMOJI_RUSHADOR = discord.PartialEmoji(
    name="rush", id=1558310698944172114
)

EMOJI_ATIRADOR = discord.PartialEmoji(
    name="atirador", id=1558310549022973973
)

EMOJI_FUZILEIRO = discord.PartialEmoji(
    name="fuzileiro", id=1558310653251297344
)

EMOJI_GRANADEIRO = discord.PartialEmoji(
    name="granadeiro", id=1558310498905227274
)

EMOJI_SUPORTE = discord.PartialEmoji(
    name="suporte", id=1558310434950610994
)

EMOJI_GUARDIOES = discord.PartialEmoji(
    name="guardioes", id=1558610184471973959
)

# ==========================================
# DISCORD
# ==========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

filas = {}
canais_squad = {}
mensagens_fila = {}
squads_em_criacao = set()
recrutamentos_em_criacao = set()


# ==========================================
# FUNCOES AUXILIARES
# ==========================================

def obter_fila(guild_id):
    if guild_id not in filas:
        filas[guild_id] = []
    return filas[guild_id]


def eh_recrutador(membro):
    if not isinstance(membro, discord.Member):
        return False

    if membro.guild_permissions.administrator:
        return True

    autorizados = {CARGO_ADM_ID, CARGO_MODERADOR_ID}
    return any(cargo.id in autorizados for cargo in membro.roles)


def obter_id_recrutado(canal):
    if not canal.topic:
        return None

    for parte in canal.topic.split():
        if parte.startswith("recrutamento_usuario:"):
            try:
                return int(parte.split(":", 1)[1])
            except ValueError:
                return None

    return None


def recrutamento_encerrado(canal):
    return bool(
        canal.topic
        and (
            "STATUS: APROVADO" in canal.topic
            or "STATUS: RECUSADO" in canal.topic
        )
    )


async def excluir_canal_recrutamento(canal):
    await asyncio.sleep(TEMPO_EXCLUSAO_CANAL)

    try:
        await canal.delete(reason="Recrutamento encerrado.")
    except discord.HTTPException as erro:
        print(f"[ERRO EXCLUIR RECRUTAMENTO] {erro}")


# ==========================================
# RECUSA DE RECRUTAMENTO
# ==========================================

class ConfirmarRecusaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar recusa",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_confirmar_recusa"
    )
    async def confirmar(self, interaction, button):
        if not eh_recrutador(interaction.user):
            await interaction.response.send_message(
                "❌ Você não tem permissão para isso.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
            await interaction.response.send_message(
                "Não consegui identificar o canal.",
                ephemeral=True
            )
            return

        if recrutamento_encerrado(canal):
            await interaction.response.send_message(
                "Este recrutamento já foi encerrado.",
                ephemeral=True
            )
            return

        recrutado_id = obter_id_recrutado(canal)

        if recrutado_id is None:
            await interaction.response.send_message(
                "Não consegui identificar o recrutado.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        membro = interaction.guild.get_member(recrutado_id)
        cargo = discord.utils.get(
            interaction.guild.roles,
            name=CARGO_RECRUTA
        )

        if membro and cargo and cargo in membro.roles:
            try:
                await membro.remove_roles(
                    cargo, reason="Recrutamento recusado."
                )
            except discord.HTTPException as erro:
                print(f"[ERRO REMOVER CARGO] {erro}")
                await interaction.edit_original_response(
                    content=(
                        "❌ Não consegui remover o cargo. "
                        "Confira as permissões do bot."
                    )
                )
                return

        try:
            await canal.edit(
                topic=(
                    f"recrutamento_usuario:{recrutado_id} "
                    "STATUS: RECUSADO"
                )
            )

            await interaction.edit_original_response(
                content="❌ **RECRUTAMENTO RECUSADO.**"
            )

            await canal.send(
                "Este recrutamento foi encerrado. "
                "O canal será excluído em alguns segundos."
            )

            await excluir_canal_recrutamento(canal)

        except discord.HTTPException as erro:
            print(f"[ERRO CONCLUIR RECUSA] {erro}")

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_cancelar_recusa"
    )
    async def cancelar(self, interaction, button):
        if not eh_recrutador(interaction.user):
            await interaction.response.send_message(
                "❌ Você não tem permissão para isso.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(
            content="Recusa cancelada.",
            view=None
        )


# ==========================================
# APROVACAO E RECUSA DE RECRUTAMENTO
# ==========================================

class RecrutamentoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Aprovar",
        emoji="✅",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_aprovar_recrutamento"
    )
    async def aprovar(self, interaction, button):
        if not eh_recrutador(interaction.user):
            await interaction.response.send_message(
                "❌ Você não tem permissão para aprovar.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
            await interaction.response.send_message(
                "Não consegui identificar o canal.",
                ephemeral=True
            )
            return

        if recrutamento_encerrado(canal):
            await interaction.response.send_message(
                "Este recrutamento já foi encerrado.",
                ephemeral=True
            )
            return

        recrutado_id = obter_id_recrutado(canal)

        if recrutado_id is None:
            await interaction.response.send_message(
                "Não consegui identificar o recrutado.",
                ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        membro = interaction.guild.get_member(recrutado_id)

        if membro is None:
            await interaction.edit_original_response(
                content="O recrutado não está mais no servidor."
            )
            return

        cargo_membro = discord.utils.get(
            interaction.guild.roles,
            name=CARGO_MEMBRO
        )
        cargo_recruta = discord.utils.get(
            interaction.guild.roles,
            name=CARGO_RECRUTA
        )

        if cargo_membro is None:
            await interaction.edit_original_response(
                content=f"Não encontrei o cargo `{CARGO_MEMBRO}`."
            )
            return

        if cargo_recruta is None:
            await interaction.edit_original_response(
                content=f"Não encontrei o cargo `{CARGO_RECRUTA}`."
            )
            return

        try:
            await membro.add_roles(
                cargo_membro, reason="Recrutamento aprovado."
            )
            await membro.remove_roles(
                cargo_recruta, reason="Recrutamento aprovado."
            )

        except discord.Forbidden:
            await interaction.edit_original_response(
                content=(
                    "❌ Não consegui alterar os cargos. "
                    "Confira a permissão Gerenciar cargos "
                    "e a hierarquia do bot."
                )
            )
            return

        except discord.HTTPException as erro:
            print(f"[ERRO ALTERAR CARGOS] {erro}")
            await interaction.edit_original_response(
                content="❌ O Discord não permitiu alterar os cargos."
            )
            return

        try:
            await canal.edit(
                topic=(
                    f"recrutamento_usuario:{recrutado_id} "
                    "STATUS: APROVADO"
                )
            )

            await interaction.edit_original_response(
                content=f"✅ **{membro.mention} FOI APROVADO!**"
            )

            await canal.send(
                f"🦁 Parabéns, {membro.mention}! "
                "Você agora faz parte da Sentinela!"
            )

            await excluir_canal_recrutamento(canal)

        except discord.HTTPException as erro:
            print(f"[ERRO CONCLUIR APROVACAO] {erro}")

    @discord.ui.button(
        label="Recusar",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_recusar_recrutamento"
    )
    async def recusar(self, interaction, button):
        if not eh_recrutador(interaction.user):
            await interaction.response.send_message(
                "❌ Você não tem permissão para recusar.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
            await interaction.response.send_message(
                "Não consegui identificar o canal.",
                ephemeral=True
            )
            return

        if recrutamento_encerrado(canal):
            await interaction.response.send_message(
                "Este recrutamento já foi encerrado.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "Tem certeza que deseja recusar este recrutamento?",
            view=ConfirmarRecusaView(),
            ephemeral=True
        )


# ==========================================
# MENSAGEM DE RECRUTAMENTO
# ==========================================

async def garantir_mensagem_recrutamento(canal, membro):
    embed = discord.Embed(
        title="🦁 𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 | 𝐑𝐄𝐂𝐑𝐔𝐓𝐀𝐌𝐄𝐍𝐓𝐎",
        description=(
            f"Salve, {membro.mention}!\n\n"
            "Este é o seu canal de recrutamento na Sentinela.\n\n"
            "Aguarde um administrador ou moderador "
            "para avaliar seu recrutamento.\n\n"
            "🦁 Boa sorte!"
        ),
        color=discord.Color.gold()
    )

    embed.set_footer(text="SENTINELA • RECRUTAMENTO")

    moderador = canal.guild.get_role(CARGO_MODERADOR_ID)
    adm = canal.guild.get_role(CARGO_ADM_ID)

    mencoes = " ".join(
        cargo.mention
        for cargo in (moderador, adm)
        if cargo is not None
    )

    async for mensagem in canal.history(limit=20):
        if mensagem.author == bot.user and mensagem.embeds:
            await mensagem.edit(
                content=mencoes or None,
                embed=embed,
                view=RecrutamentoView(),
                allowed_mentions=discord.AllowedMentions(
                    roles=True, users=True
                )
            )
            return

    await canal.send(
        content=mencoes or None,
        embed=embed,
        view=RecrutamentoView(),
        allowed_mentions=discord.AllowedMentions(
            roles=True, users=True
        )
    )


async def criar_recrutamento(membro):
    guild = membro.guild

    if membro.id in recrutamentos_em_criacao:
        return

    recrutamentos_em_criacao.add(membro.id)

    try:
        topico = f"recrutamento_usuario:{membro.id}"

        for canal_existente in guild.text_channels:
            if (
                canal_existente.topic
                and topico in canal_existente.topic
                and not recrutamento_encerrado(canal_existente)
            ):
                await garantir_mensagem_recrutamento(
                    canal_existente, membro
                )
                return

        categoria = guild.get_channel(CATEGORIA_RECRUTAMENTO_ID)

        permissoes = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            membro: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )
        }

        for cargo_id in (CARGO_MODERADOR_ID, CARGO_ADM_ID):
            cargo = guild.get_role(cargo_id)
            if cargo:
                permissoes[cargo] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )

        if guild.me:
            permissoes[guild.me] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True
            )

        nome_canal = f"recrutamento-{membro.name}".lower()
        nome_canal = nome_canal.replace(" ", "-")[:90]

        canal = await guild.create_text_channel(
            name=nome_canal,
            category=(
                categoria
                if isinstance(categoria, discord.CategoryChannel)
                else None
            ),
            overwrites=permissoes,
            topic=topico,
            reason="Novo recrutamento Sentinela."
        )

        await garantir_mensagem_recrutamento(canal, membro)
        print(f"[RECRUTAMENTO] Canal criado para {membro}.")

    except discord.Forbidden:
        print(
            "[RECRUTAMENTO] Sem permissão para criar canal. "
            "Confira Gerenciar canais."
        )

    except discord.HTTPException as erro:
        print(f"[ERRO CRIAR RECRUTAMENTO] {erro}")

    finally:
        recrutamentos_em_criacao.discard(membro.id)


# ==========================================
# FILA DA GUERRA DE GUILDA
# ==========================================

def criar_embed_fila(guild_id):
    fila = obter_fila(guild_id)

    embed = discord.Embed(
        title="𝐆𝐔𝐄𝐑𝐑𝐀 𝐃𝐄 𝐆𝐔𝐈𝐋𝐃𝐀",
        description="**FORME SEU SQUAD E AMASSE GERAL NA GUERRA!**",
        color=discord.Color.gold()
    )

    embed.add_field(
        name=f"{EMOJI_SQUAD} JOGADORES NA FILA",
        value=f"**{len(fila)} / {LIMITE_FILA} jogadores**",
        inline=False
    )

    if fila:
        jogadores = []

        for indice, jogador in enumerate(fila, start=1):
            jogadores.append(
                f"**{indice}.** <@{jogador['id']}>\n"
                f"{jogador['emoji']} **{jogador['funcao']}**"
            )

        embed.add_field(
            name="\u200b",
            value="\n\n".join(jogadores),
            inline=False
        )
    else:
        embed.add_field(
            name="\u200b",
            value="A fila está vazia. Entre e forme seu squad!",
            inline=False
        )

    embed.set_footer(text="SENTINELA • GUERRA DE GUILDA")
    embed.set_thumbnail(url=EMOJI_SENTINELA_URL)

    return embed


async def atualizar_mensagem_fila(guild):
    dados = mensagens_fila.get(guild.id)

    if not dados:
        return

    canal_id, mensagem_id = dados
    canal = guild.get_channel(canal_id)

    if not isinstance(canal, discord.TextChannel):
        return

    try:
        mensagem = await canal.fetch_message
