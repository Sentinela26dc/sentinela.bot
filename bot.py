
import os
import json
import asyncio
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
        mensagem = await canal.fetch_message(mensagem_id)
        await mensagem.edit(
            embed=criar_embed_fila(guild.id),
            view=FilaView()
        )

    except discord.NotFound:
        print("[FILA] A mensagem da fila foi apagada.")

    except discord.Forbidden:
        print("[FILA] Sem permissão para editar a mensagem.")

    except discord.HTTPException as erro:
        print(f"[ERRO ATUALIZAR FILA] {erro}")


async def criar_canal_squad(guild, fila):
    canal_anterior_id = canais_squad.get(guild.id)

    if canal_anterior_id:
        canal_anterior = guild.get_channel(canal_anterior_id)
        if canal_anterior:
            try:
                await canal_anterior.delete(
                    reason="Preparando um novo squad."
                )
            except discord.HTTPException as erro:
                print(f"[ERRO EXCLUIR CANAL ANTERIOR] {erro}")

    permissoes = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False
        )
    }

    for jogador in fila:
        membro = guild.get_member(jogador["id"])
        if membro:
            permissoes[membro] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True
            )

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

    canal = await guild.create_text_channel(
        name="🔒・squad-sentinela",
        overwrites=permissoes,
        reason="Fila da Guerra de Guilda completa."
    )

    canais_squad[guild.id] = canal.id

    mencoes = "\n".join(
        f"<@{jogador['id']}> — {jogador['emoji']} "
        f"**{jogador['funcao']}**"
        for jogador in fila
    )

    await canal.send(
        "🦁 **SQUAD COMPLETO!**\n\n"
        f"{mencoes}\n\n"
        "Organizem-se para a Guerra de Guilda e boa sorte!"
    )

    return canal


# ==========================================
# REGISTRAR JOGADOR
# ==========================================

async def registrar_jogador(interaction, funcao, emoji):
    guild = interaction.guild

    if guild is None:
        await interaction.response.send_message(
            "Não consegui identificar o servidor.",
            ephemeral=True
        )
        return

    await interaction.response.defer(ephemeral=True, thinking=True)

    fila = obter_fila(guild.id)
    membro_id = interaction.user.id

    if any(j["id"] == membro_id for j in fila):
        await interaction.edit_original_response(
            content="⚠️ Você já está na fila!",
            view=None
        )
        return

    if len(fila) >= LIMITE_FILA:
        await interaction.edit_original_response(
            content="❌ A fila já está completa!",
            view=None
        )
        return

    fila.append({
        "id": membro_id,
        "funcao": funcao,
        "emoji": str(emoji)
    })

    await interaction.edit_original_response(
        content=f"✅ Você entrou na fila como **{funcao}**!",
        view=None
    )

    try:
        await atualizar_mensagem_fila(guild)

        if (
            len(fila) == LIMITE_FILA
            and guild.id not in squads_em_criacao
        ):
            squads_em_criacao.add(guild.id)
            try:
                await criar_canal_squad(guild, list(fila))
            finally:
                squads_em_criacao.discard(guild.id)

    except Exception as erro:
        print(
            f"[ERRO PROCESSAMENTO FILA] "
            f"{type(erro).__name__}: {erro!r}"
        )


# ==========================================
# ESCOLHA DE FUNCAO
# ==========================================

class EscolherFuncaoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(
        label="Rushador",
        emoji=EMOJI_RUSHADOR,
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def rushador(self, interaction, button):
        await registrar_jogador(
            interaction, "Rushador", EMOJI_RUSHADOR
        )

    @discord.ui.button(
        label="Fuzileiro",
        emoji=EMOJI_FUZILEIRO,
        style=discord.ButtonStyle.secondary,
        row=0
    )
    async def fuzileiro(self, interaction, button):
        await registrar_jogador(
            interaction, "Fuzileiro", EMOJI_FUZILEIRO
        )

    @discord.ui.button(
        label="Atirador",
        emoji=EMOJI_ATIRADOR,
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def atirador(self, interaction, button):
        await registrar_jogador(
            interaction, "Atirador", EMOJI_ATIRADOR
        )

    @discord.ui.button(
        label="Suporte",
        emoji=EMOJI_SUPORTE,
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def suporte(self, interaction, button):
        await registrar_jogador(
            interaction, "Suporte", EMOJI_SUPORTE
        )

    @discord.ui.button(
        label="Granadeiro",
        emoji=EMOJI_GRANADEIRO,
        style=discord.ButtonStyle.secondary,
        row=1
    )
    async def granadeiro(self, interaction, button):
        await registrar_jogador(
            interaction, "Granadeiro", EMOJI_GRANADEIRO
        )


# ==========================================
# BOTOES PRINCIPAIS DA FILA
# ==========================================

class FilaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="ENTRAR NA FILA",
        emoji=EMOJI_ENTRAR,
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_entrar_fila"
    )
    async def entrar(self, interaction, button):
        try:
            guild = interaction.guild

            if guild is None:
                await interaction.response.send_message(
                    "❌ Esse botão só funciona no servidor.",
                    ephemeral=True
                )
                return

            fila = obter_fila(guild.id)
            membro_id = interaction.user.id

            if any(j["id"] == membro_id for j in fila):
                await interaction.response.send_message(
                    "⚠️ Você já está na fila!",
                    ephemeral=True
                )
                return

            if len(fila) >= LIMITE_FILA:
                await interaction.response.send_message(
                    "❌ A fila já está completa!",
                    ephemeral=True
                )
                return

            await interaction.response.send_message(
                content=(
                    "**🎮 ESCOLHA SUA FUNÇÃO**\n"
                    "Selecione sua função para a Guerra de Guilda:"
                ),
                view=EscolherFuncaoView(),
                ephemeral=True
            )

            print(
                f"[FILA] Menu enviado para {interaction.user} "
                f"(ID {interaction.user.id})."
            )

        except Exception as erro:
            print(
                f"[ERRO AO ABRIR FUNCOES] "
                f"{type(erro).__name__}: {erro!r}"
            )

            try:
                if not interaction.response.is_done():
                    await interaction.response.send_message(
                        "❌ Não consegui abrir as funções. "
                        "Tente novamente.",
                        ephemeral=True
                    )
            except Exception as erro_resposta:
                print(f"[ERRO AO RESPONDER] {erro_resposta!r}")

    @discord.ui.button(
        label="SAIR DA FILA",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_sair_fila"
    )
    async def sair(self, interaction, button):
        try:
            await interaction.response.defer(
                ephemeral=True, thinking=True
            )

            guild = interaction.guild

            if guild is None:
                await interaction.edit_original_response(
                    content="❌ Não consegui identificar o servidor.",
                    view=None
                )
                return

            fila = obter_fila(guild.id)
            membro_id = interaction.user.id

            indice = next(
                (
                    i for i, jogador in enumerate(fila)
                    if jogador["id"] == membro_id
                ),
                None
            )

            if indice is None:
                await interaction.edit_original_response(
                    content="⚠️ Você não está na fila.",
                    view=None
                )
                return

            fila.pop(indice)
            canal_id = canais_squad.pop(guild.id, None)

            if canal_id:
                canal = guild.get_channel(canal_id)
                if canal:
                    try:
                        await canal.delete(
                            reason="Um jogador saiu da fila."
                        )
                    except discord.HTTPException as erro:
                        print(f"[ERRO EXCLUIR SQUAD] {erro}")

            await atualizar_mensagem_fila(guild)

            await interaction.edit_original_response(
                content="✅ Você saiu da fila!",
                view=None
            )

        except Exception as erro:
            print(
                f"[ERRO BOTAO SAIR] "
                f"{type(erro).__name__}: {erro!r}"
            )

            try:
                if interaction.response.is_done():
                    await interaction.edit_original_response(
                        content="❌ Ocorreu um erro ao sair da fila.",
                        view=None
                    )
                else:
                    await interaction.response.send_message(
                        "❌ Ocorreu um erro ao sair da fila.",
                        ephemeral=True
                    )
            except Exception as erro_resposta:
                print(f"[ERRO RESPOSTA SAIR] {erro_resposta!r}")


# ==========================================
# COMANDOS
# ==========================================

@bot.command()
async def ping(ctx):
    await ctx.send("🏓 Pong! Sentinela está online.")


@bot.command()
async def sentinela(ctx):
    await ctx.send(
        "🦁 **SENTINELA**\n"
        "A tropa está na área!"
    )


@bot.command()
async def ajuda(ctx):
    await ctx.send(
        "**🦁 COMANDOS SENTINELA**\n\n"
        "`!ping` — testa o bot\n"
        "`!sentinela` — mensagem da guilda\n"
        "`!ajuda` — mostra os comandos\n"
        "`!fila` — publica a fila da Guerra de Guilda\n"
        "`!listaremojis` — lista os emojis do servidor\n"
        "`!publicarpasse` — publica o anúncio do passe Booyah"
    )


@bot.command()
@commands.has_permissions(manage_guild=True)
async def fila(ctx):
    if ctx.guild is None:
        return

    mensagem = await ctx.send(
        embed=criar_embed_fila(ctx.guild.id),
        view=FilaView()
    )

    mensagens_fila[ctx.guild.id] = (
        ctx.channel.id,
        mensagem.id
    )

    print(
        f"[FILA] Mensagem publicada. "
        f"Canal={ctx.channel.id}, mensagem={mensagem.id}"
    )


@fila.error
async def fila_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ Você precisa da permissão **Gerenciar servidor** "
            "para publicar a fila."
        )
    else:
        print(f"[ERRO COMANDO FILA] {error!r}")


@bot.command()
@commands.has_permissions(administrator=True)
async def listaremojis(ctx):
    linhas = [
        f"{emoji} — `{emoji.id}`"
        for emoji in ctx.guild.emojis
    ]

    if not linhas:
        await ctx.send(
            "Não encontrei emojis personalizados neste servidor."
        )
        return

    texto = "\n".join(linhas)

    for inicio in range(0, len(texto), 1800):
        await ctx.send(texto[inicio:inicio + 1800])


# ==========================================
# SISTEMA DE AQUISICAO DE TICKETS
# ==========================================

PRECO_TICKET_CENTAVOS = 50
ARQUIVO_PARTICIPANTES_PASSE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "participantes_passe.json"
)


def carregar_dados_passe():
    try:
        with open(ARQUIVO_PARTICIPANTES_PASSE, "r", encoding="utf-8") as arquivo:
            dados = json.load(arquivo)
        if not isinstance(dados, dict):
            raise ValueError("Formato de dados inválido")
        dados.setdefault("participantes", {})
        dados.setdefault("anuncio", None)
        return dados
    except FileNotFoundError:
        return {"participantes": {}, "anuncio": None}
    except (json.JSONDecodeError, OSError, ValueError) as erro:
        print(f"[ERRO LER PARTICIPANTES DO PASSE] {erro!r}")
        return {"participantes": {}, "anuncio": None}


def salvar_dados_passe():
    temporario = ARQUIVO_PARTICIPANTES_PASSE + ".tmp"
    with open(temporario, "w", encoding="utf-8") as arquivo:
        json.dump(dados_passe, arquivo, ensure_ascii=False, indent=2)
    os.replace(temporario, ARQUIVO_PARTICIPANTES_PASSE)


dados_passe = carregar_dados_passe()


def formatar_reais(centavos):
    reais = centavos // 100
    centavos_restantes = centavos % 100
    return f"R$ {reais:,}".replace(",", ".") + (
        f",{centavos_restantes:02d}"
    )


class QuantidadeTicketsModal(discord.ui.Modal):
    def __init__(self):
        super().__init__(title="Adquirir Tickets")

        self.quantidade = discord.ui.TextInput(
            label="Quantidade de tickets",
            placeholder="Digite quantos tickets deseja (ex.: 12)",
            required=True,
            min_length=1,
            max_length=5
        )
        self.add_item(self.quantidade)

    async def on_submit(self, interaction: discord.Interaction):
        texto = str(self.quantidade.value).strip()

        if not texto.isdigit():
            await interaction.response.send_message(
                "❌ Digite somente um número inteiro positivo.",
                ephemeral=True
            )
            return

        quantidade = int(texto)

        if quantidade < 1 or quantidade > 99999:
            await interaction.response.send_message(
                "❌ Escolha uma quantidade entre 1 e 99.999 tickets.",
                ephemeral=True
            )
            return

        total_centavos = quantidade * PRECO_TICKET_CENTAVOS

        embed = discord.Embed(
            title=(
                "<a:ac_presente_tkf15259294509806429:1561924913571569716> "
                "𝐂𝐎𝐍𝐅𝐈𝐑𝐌𝐀𝐑 𝐂𝐎𝐌𝐏𝐑𝐀 𝐃𝐎𝐒 𝐓𝐈𝐂𝐊𝐄𝐓𝐒"
            ),
            description=(
                f"Salve, {interaction.user.mention}!\n\n"
                "**Confira os dados da sua solicitacao "
                "antes de continuar.**"
            ),
            color=discord.Color.gold()
        )

        embed.add_field(
            name="<:Emoji_0006_silhuetadecaminhaodee:1562282301155573810> Quantidade",
            value=f"**{quantidade:,} tickets**".replace(",", "."),
            inline=True
        )

        embed.add_field(
            name="<:cifrao_sentry:1563067820131098624> Preco por ticket",
            value=f"**{formatar_reais(PRECO_TICKET_CENTAVOS)}**",
            inline=True
        )

        embed.add_field(
            name="<:faturamento_sentry:1563062715222720574> Valor total",
            value=f"**{formatar_reais(total_centavos)}**",
            inline=False
        )

        embed.add_field(
            name="<:suporte_sentry:1563328550629675018> 𝐏𝐑𝐀𝐙𝐎 𝐃𝐄 𝐀𝐓𝐄𝐍𝐃𝐈𝐌𝐄𝐍𝐓𝐎",
            value=(
                "<:ponto_amarelo_lunar_215259154756:1562283913827586119> "
                "<a:ayellow_parceiro1525943180707495:1562282610443419688> "
                "Um administrador irá atender você e enviar a chave PIX "
                "em até **5 𝑀𝐼𝑁𝑈𝑇𝑂𝑆**."
            ),
            inline=False
        )
        embed.set_footer(
            text="SENTINELA • PASSE BOOYAH"
        )
        await interaction.response.send_message(
            embed=embed,
            view=ConfirmarCompraView(
                comprador_id=interaction.user.id,
                quantidade=quantidade
            ),
            ephemeral=True
        )


class ConfirmarCompraView(discord.ui.View):
    def __init__(self, comprador_id: int, quantidade: int):
        super().__init__(timeout=300)
        self.comprador_id = comprador_id
        self.quantidade = quantidade

    async def interaction_check(
        self, interaction: discord.Interaction
    ) -> bool:
        if interaction.user.id != self.comprador_id:
            await interaction.response.send_message(
                "❌ Esta confirmação pertence a outro jogador.",
                ephemeral=True
            )
            return False
        return True

    @discord.ui.button(
        label="CONFIRMAR COMPRA",
        style=discord.ButtonStyle.secondary
    )
    async def confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                "❌ Este botão só funciona dentro do servidor.",
                ephemeral=True
            )
            return

        await interaction.response.defer(
            ephemeral=True, thinking=True
        )

        comprador = interaction.user
        total_centavos = (
            self.quantidade * PRECO_TICKET_CENTAVOS
        )

        permissoes = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False
            ),
            comprador: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True
            )
        }

        for cargo_id in (CARGO_ADM_ID, CARGO_MODERADOR_ID):
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

     
        nome_seguro = "".join(
            caractere.lower()
            if caractere.isalnum() else "-"
            for caractere in comprador.name
        ).strip("-")[:40] or "jogador"

        try:
            canal_compra = await guild.create_text_channel(
                name=f"tickets-{nome_seguro}",
                overwrites=permissoes,
                topic=(
                    f"compra_tickets_usuario:{comprador.id} "
                    f"quantidade:{self.quantidade} "
                    "STATUS: AGUARDANDO PAGAMENTO"
                ),
                reason="Solicitacao de tickets do Passe Booyah"
            )

            embed_compra = discord.Embed(
                title="𝐒𝐎𝐋𝐈𝐂𝐈𝐓𝐀ÇÃ𝐎 𝐃𝐄 𝐓𝐈𝐂𝐊𝐄𝐓𝐒",
                description=(
                    f"Salve, {comprador.mention}!\n\n"
                    "<:suporte_sentry:1563328550629675018> "
                    "**Sua solicitação foi registrada com sucesso!**\n\n"
                    "Aguarde até que um administrador venha atender você."
                ),
                color=discord.Color.gold()
            )

            embed_compra.add_field(
                name="<:Personagem_Sentry:1563331978110046300>  Comprador",
                value=f"{comprador.mention}",
                inline=False
            )

            embed_compra.add_field(
                name="<:Emoji_0006_silhuetadecaminhaodee:1562282301155573810> Quantidade solicitada",
                value=f"**{self.quantidade:,} tickets**".replace(",", "."),
                inline=True
            )

            embed_compra.add_field(
                name="<:cifrao_sentry:1563067820131098624> Preço unitário",
                value=f"**{formatar_reais(PRECO_TICKET_CENTAVOS)}**",
                inline=True
            )

            embed_compra.add_field(
                name="<:faturamento_sentry:1563062715222720574> Valor total",
                value=f"**{formatar_reais(total_centavos)}**",
                inline=False
            )

            embed_compra.set_footer(
                text="SENTINELA • PASSE BOOYAH"
            )
            await canal_compra.send(
                content=(
                    f"Salve, {comprador.mention}!\n\n"
                    "||"
                    "<@&1556441469978411032> "
                    "<@&1556530332281344082>"
                    "||"
                ),
                embed=embed_compra,
                view=ConfirmarPagamentoView(),
                allowed_mentions=discord.AllowedMentions(
                    users=True,
                    roles=True,
                    everyone=False
                )
            )

            await interaction.edit_original_response(
                content=(
                    f"✅ Sua solicitação foi criada!\n"
                    f"Canal privado: {canal_compra.mention}\n"
                    f"**Quantidade:** {self.quantidade} tickets\n"
                    f"**Total:** {formatar_reais(total_centavos)}"
                ),
                view=None
            )

            self.stop()

        except discord.Forbidden:
            await interaction.edit_original_response(
                content=(
                    "❌ Não consegui criar o canal privado. "
                    "Confira se o bot tem as permissões "
                    "**Gerenciar canais** e **Ver canais**."
                ),
                view=None
            )

        except discord.HTTPException as erro:
            print(f"[ERRO CRIAR COMPRA] {erro!r}")
            await interaction.edit_original_response(
                content=(
                    "❌ O Discord não permitiu criar o canal. "
                    "Tente novamente ou avise a administração."
                ),
                view=None
            )

    @discord.ui.button(
        label="CANCELAR COMPRA",
        style=discord.ButtonStyle.secondary
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="❌ Solicitação cancelada.",
            embed=None,
            view=None
        )


class AdquirirTicketsView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        total_participantes = len(dados_passe["participantes"])
        for item in self.children:
            if getattr(item, "custom_id", None) == "sentinela_participantes":
                item.label = f"PARTICIPANTES ({total_participantes})"

    @discord.ui.button(
        label="ADQUIRIR TICKETS",
        emoji="<a:aabcyellowestrelatkf152591544208:1561953163840462952>",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_adquirir_tickets"
    )
    async def adquirir(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_modal(
            QuantidadeTicketsModal()
        )

    @discord.ui.button(
        label="PARTICIPANTES (0)",
        emoji="<:membros_sentry:1564489956766916698>",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_participantes"
    )
    async def participantes(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        registros = dados_passe["participantes"]
        total_participantes = len(registros)
        embed = discord.Embed(
            title="𝐏𝐀𝐑𝐓𝐈𝐂𝐈𝐏𝐀𝐍𝐓𝐄𝐒 𝐃𝐎 𝐏𝐀𝐒𝐒𝐄 𝐁𝐎𝐎𝐘𝐀𝐇",
            description=(
                f"Participantes com pagamento confirmado: **{total_participantes}**"
            ),
            color=discord.Color.gold()
        )

        if not registros:
            embed.add_field(
                name="Ainda não há participantes",
                value="Os jogadores aparecerão aqui após a confirmação do pagamento por um administrador.",
                inline=False
            )
        else:
            ordenados = sorted(
                registros.values(),
                key=lambda registro: int(registro.get("tickets", 0)),
                reverse=True
            )
            limite = 75
            ordenados_visiveis = ordenados[:limite]
            for inicio in range(0, len(ordenados_visiveis), 15):
                grupo = ordenados_visiveis[inicio:inicio + 15]
                linhas = [
                    f"**{registro.get('nome', 'Jogador')}** — "
                    f"{int(registro.get('tickets', 0)):,} tickets".replace(",", ".")
                    for registro in grupo
                ]
                embed.add_field(
                    name=(
                        "Participantes e tickets confirmados"
                        if inicio == 0 else "Continuação"
                    ),
                    value="\n".join(linhas)[:1024],
                    inline=False
                )
            if len(ordenados) > limite:
                embed.add_field(
                    name="Lista parcial",
                    value=f"E mais {len(ordenados) - limite} participantes não exibidos nesta lista.",
                    inline=False
                )

        embed.set_footer(text="SENTINELA • PASSE BOOYAH")
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ConfirmarPagamentoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="CONFIRMAR PAGAMENTO",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_confirmar_pagamento_passe"
    )
    async def confirmar_pagamento(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not eh_recrutador(interaction.user):
            await interaction.response.send_message(
                "Você não tem permissão para confirmar pagamentos.",
                ephemeral=True
            )
            return

        canal = interaction.channel
        if not isinstance(canal, discord.TextChannel) or not canal.topic:
            await interaction.response.send_message(
                "Não consegui identificar os dados desta compra.",
                ephemeral=True
            )
            return

        if "STATUS: PAGAMENTO CONFIRMADO" in canal.topic:
            await interaction.response.send_message(
                "Este pagamento já foi confirmado anteriormente.",
                ephemeral=True
            )
            return

        if "STATUS: AGUARDANDO PAGAMENTO" not in canal.topic:
            await interaction.response.send_message(
                "Este canal não está aguardando confirmação de pagamento.",
                ephemeral=True
            )
            return

        dados_topico = {}
        for parte in canal.topic.split():
            if ":" in parte:
                chave, valor = parte.split(":", 1)
                if chave in ("compra_tickets_usuario", "quantidade"):
                    try:
                        dados_topico[chave] = int(valor)
                    except ValueError:
                        pass

        comprador_id = dados_topico.get("compra_tickets_usuario")
        quantidade = dados_topico.get("quantidade")
        if not comprador_id or not quantidade or quantidade < 1:
            await interaction.response.send_message(
                "Não consegui ler o comprador ou a quantidade neste canal.",
                ephemeral=True
            )
            return

        membro = interaction.guild.get_member(comprador_id) if interaction.guild else None
        if membro is None and interaction.guild:
            try:
                membro = await interaction.guild.fetch_member(comprador_id)
            except discord.HTTPException:
                membro = None
        nome = membro.display_name if membro else f"Usuário {comprador_id}"

        tinha_registro_anterior = str(comprador_id) in dados_passe["participantes"]
        registro_anterior = dict(
            dados_passe["participantes"].get(str(comprador_id), {})
        )
        registro = dados_passe["participantes"].get(str(comprador_id), {
            "nome": nome,
            "tickets": 0
        })
        registro["nome"] = nome
        registro["tickets"] = int(registro.get("tickets", 0)) + quantidade
        dados_passe["participantes"][str(comprador_id)] = registro

        novo_topico = canal.topic.replace(
            "STATUS: AGUARDANDO PAGAMENTO",
            "STATUS: PAGAMENTO CONFIRMADO"
        )
        try:
            await canal.edit(
                topic=novo_topico,
                reason=f"Pagamento confirmado por {interaction.user}"
            )
            salvar_dados_passe()
        except (discord.HTTPException, OSError) as erro:
            if tinha_registro_anterior:
                dados_passe["participantes"][str(comprador_id)] = registro_anterior
            else:
                dados_passe["participantes"].pop(str(comprador_id), None)
            try:
                salvar_dados_passe()
            except OSError:
                pass
            try:
                await canal.edit(
                    topic=novo_topico.replace(
                        "STATUS: PAGAMENTO CONFIRMADO",
                        "STATUS: AGUARDANDO PAGAMENTO"
                    ),
                    reason="Reverter confirmação que não pôde ser salva"
                )
            except discord.HTTPException:
                pass
            await interaction.response.send_message(
                f"Não consegui salvar a confirmação: {erro}",
                ephemeral=True
            )
            return

        try:
            await atualizar_anuncio_participantes()
        except Exception as erro:
            print(f"[ERRO ATUALIZAR BOTAO PARTICIPANTES] {erro!r}")

        await interaction.response.edit_message(view=None)
        await interaction.followup.send(
            (
                f"✅ Pagamento confirmado por {interaction.user.mention}. "
                f"Foram registrados {quantidade:,} tickets para {nome}."
            ).replace(",", "."),
            ephemeral=True
        )

async def atualizar_anuncio_participantes():
    anuncio = dados_passe.get("anuncio")
    if not anuncio:
        return

    canal_id = anuncio.get("canal_id")
    mensagem_id = anuncio.get("mensagem_id")
    if not canal_id or not mensagem_id:
        return

    canal = bot.get_channel(canal_id)
    if canal is None:
        canal = await bot.fetch_channel(canal_id)
    mensagem = await canal.fetch_message(mensagem_id)
    await mensagem.edit(view=AdquirirTicketsView())


# ==========================================
# PUBLICAR ANUNCIO DO PASSE BOOYAH
# ==========================================

@bot.command(name="publicarpasse")
@commands.has_permissions(administrator=True)
async def publicarpasse(ctx):
    try:
        canal = bot.get_channel(CANAL_PASSE_BOOYAAH_ID)

        if canal is None:
            canal = await bot.fetch_channel(
                CANAL_PASSE_BOOYAAH_ID
            )

        if not isinstance(canal, discord.TextChannel):
            await ctx.send(
                "❌ O canal não é um canal de texto."
            )
            return

        caminho_imagem = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "passe_booyah.jpg"
        )

        if not os.path.isfile(caminho_imagem):
            await ctx.send(
                "❌ Não encontrei passe_booyah.jpg na pasta do bot."
            )
            return


        # TITULO E DESCRICAO
        embed = discord.Embed(
            title=(
                f"{EMOJI_TITULO_PASSE} "
                "𝐒𝐎𝐑𝐓𝐄𝐈𝐎 𝐃𝐄 𝐏𝐀𝐒𝐒𝐄 𝐁𝐎𝐎𝐘𝐀𝐇"
            ),
            color=discord.Color.gold()
        )

        # IMAGEM NO TOPO
        embed.set_image(
            url="attachment://passe_booyah.jpg"
        )

        # VALOR POR TICKET
        embed.add_field(
            name=(
                f"{EMOJI_CARRINHO_PASSE} "
                "𝐕𝐀𝐋𝐎𝐑 𝐏𝐎𝐑 𝐓𝐈𝐂𝐊𝐄𝐓"
            ),
            value=(
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                f"{EMOJI_DINHEIRO_PASSE} "
                "**R$ 0,50 por ticket**\n"
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                "<:Emoji_0006_silhuetadecaminhaodee:1562282301155573810> "
                "**A quantidade de compra dos tickets "
                "sao ilimitadas**"
            ),
            inline=False
        )

        # INICIO DO EVENTO
        embed.add_field(
            name=(
                f"{EMOJI_INICIO_EVENTO_PASSE} "
                "𝐈𝐍𝐈́𝐂𝐈𝐎 𝐃𝐎 𝐄𝐕𝐄𝐍𝐓𝐎"
            ),
            value=(
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                f"{EMOJI_ESTRELA_PASSE} "
                "**Data de inicio: 25/10/2026**\n"
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                f"{EMOJI_TROFEU_PASSE} "
                "Todas as informacoes sobre o evento serao divulgadas "
                "no canal <#1556527447669997568>, incluindo o anuncio "
                "do ganhador.\n"
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                f"{EMOJI_AVISO_EVENTO_PASSE} "
                "Fique atento aos avisos da administracao "
                "para nao perder nenhuma novidade!"
            ),
            inline=False
        )

        # TRANSPARENCIA
        embed.add_field(
            name=(
                f"{EMOJI_TRANSPARENCIA_PASSE} "
                "𝐓𝐑𝐀𝐍𝐒𝐏𝐀𝐑𝐄̂𝐍𝐂𝐈𝐀"
            ),
            value=(
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                f"{EMOJI_DUVIDAS_PASSE} "
                "A compra sera acompanhada pela administracao.\n"
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                f"{EMOJI_VERIFICADO_PASSE} "
                "Sorteio transparente.\n"
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                f"{EMOJI_SUPORTE_PASSE} "
                "Resultado divulgado no servidor."
            ),
            inline=False
        )

        # COMO PARTICIPAR
        embed.add_field(
            name=(
                f"{EMOJI_PIX_PASSE} "
                f"{EMOJI_MASTERCARD_PASSE} "
                "𝐂𝐎𝐌𝐎 𝐏𝐀𝐑𝐓𝐈𝐂𝐈𝐏𝐀𝐑"
            ),
            value=(
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                "**Requisito:** ter jogado pelo menos uma partida "
                "com algum membro da guilda Sentinela.\n"
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                "<:faturamento_sentry:1563062715222720574> "
                "**Compra de tickets:** clique no botao abaixo "
                "para comprar e informe a quantidade desejada.\n"
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                "<:amarelo_lunar:1561925242258067626> "
                "**Atendimento privado:** voce sera direcionado "
                "para um canal privado com a administracao.\n"
                f"{EMOJI_PONTO_AMARELO_PASSE} "
                f"{EMOJI_PIX_PASSE} "
                "**Pagamento via Pix:** um administrador enviara "
                "a chave Pix para voce realizar o pagamento."
            ),
            inline=False
        )

        embed.set_footer(
            text="SENTINELA • PASSE BOOYAH"
        )

        arquivo = discord.File(
            caminho_imagem,
            filename="passe_booyah.jpg"
        )

        mensagem_anuncio = await canal.send(
            embed=embed,
            file=arquivo,
            view=AdquirirTicketsView()
        )
        dados_passe["anuncio"] = {
            "canal_id": canal.id,
            "mensagem_id": mensagem_anuncio.id
        }
        salvar_dados_passe()

        await ctx.send(
            "Anuncio do Passe Booyah publicado com sucesso!"
        )

    except Exception as erro:
        print(
            f"[ERRO PUBLICAR PASSE] "
            f"{type(erro).__name__}: {erro!r}"
        )
        await ctx.send(
            f"Ocorreu um erro ao publicar o passe: {erro}"
        )

# ==========================================
# INICIAR BOT
# ==========================================

if not TOKEN:
    raise RuntimeError(
        "A variável DISCORD_TOKEN não foi configurada no Railway."
    )

bot.add_view(AdquirirTicketsView())
bot.add_view(ConfirmarPagamentoView())

bot.run(TOKEN)
