import os
import json
import asyncio
import io
import discord
from PIL import Image, ImageDraw, ImageFont, ImageOps
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
# EMOJIS DO PASSE BOOYAH
# ==========================================

EMOJI_TOPICO_PASSE = discord.PartialEmoji(
    name="a13893yellowdot15259153968871548",
    id=1561925909852852264,
    animated=True
)

EMOJI_TRANSPARENCIA_PASSE = discord.PartialEmoji(
    name="ayellow_parceiro1525943180707495",
    id=1562282610443419688,
    animated=True
)

EMOJI_TITULO_PASSE = discord.PartialEmoji(
    name="ac_presente_tkf15259294509806429",
    id=1561924913571569716,
    animated=True
)

EMOJI_INICIO_EVENTO_PASSE = discord.PartialEmoji(
    name="asino1477300288510623806",
    id=1562309472330973194,
    animated=True
)

EMOJI_AVISO_EVENTO_PASSE = discord.PartialEmoji(
    name="aavisoaura1525915447445164112",
    id=1562307850485899305,
    animated=True
)

EMOJI_DUVIDAS_PASSE = discord.PartialEmoji(
    name="amarelo_lunar1525915443737657484",
    id=1561925242258067626
)

EMOJI_VERIFICADO_PASSE = (
    "<:VERIFICADO1525915435835457618:1561950871518978058>"
)

EMOJI_ESTRELA_PASSE = (
    "<a:aabcyellowestrelatkf152591544208:1561953163840462952>"
)

EMOJI_CARRINHO_PASSE = (
    "<:8916shoppingcart:1559026055170367508>"
)

EMOJI_SUPORTE_PASSE = (
    "<:suporte_sentry:1563328550629675018>"
)

EMOJI_TICKET_PASSE = (
    "<:ticket_free:1561947176249069658>"
)

EMOJI_PIX_PASSE = "<:7406pix:1559018337558863933>"

EMOJI_MASTERCARD_PASSE = (
    "<a:207799mastercard:1559019335492706324>"
)

EMOJI_DINHEIRO_PASSE = (
    "<a:999284cash:1559012499016261713>"
)

EMOJI_PONTO_AMARELO_PASSE = (
    "<:ponto_amarelo_lunar_215259154756:1562283913827586119>"
)

EMOJI_TROFEU_PASSE = discord.PartialEmoji(
    name="Pixelated_trophy_design__Pixel_g",
    id=1562669175456014376
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
