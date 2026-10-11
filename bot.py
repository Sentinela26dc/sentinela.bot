
import os
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
            await ctx.send("❌ O canal não é um canal de texto.")
            return

        await canal.send(URL_IMAGEM_PASSE)

        embed = discord.Embed(
            title=(
                "<:PASSE_BOOYAH:1558634919985680454> "
                "𝐒𝐎𝐑𝐓𝐄𝐈𝐎 𝐃𝐄 𝐏𝐀𝐒𝐒𝐄 𝐁𝐎𝐎𝐘𝐀𝐇"
            ),
            description=(
                "<:Sentry:1558683706489708634> "
                "**EVENTO SENTINELA — PASSE BOOYAH**"
            ),
            color=discord.Color.gold()
        )

        embed.add_field(
            name="🎟️ Inscrição",
            value="**R$ 0,50**",
            inline=False
        )

        embed.add_field(
            name="<:Discord_members:1558695527556849744> **QUANTIDADE MÍNIMA**",
            value="10 participantes confirmados.",
            inline=False
        )

        embed.add_field(
            name="📅 Início do evetinto",
            value="**15/10/2026**",
            inline=False
        )

        embed.add_field(
            name="<a:AI_Boost_crystal:1558664770473959555> BENEFÍCIO EXCLUSIVO",
            value=(
                "**Impulsionadores tem direito "
                "a 1 ticket gratuito por mês!**"
            ),
            inline=False
        )

        embed.add_field(
            name="<a:check_discord:1558664467594612816> ATENÇÃO, SENTINELAS!",
            value=(
                "**Se o número mínimo de participantes não for atingido até o início do evento, os participantes que pagaram receberão o reembolso.**"
            ),
            inline=False
        )

        # O emoji aparece como icone do rodape.
        embed.set_footer(
            text="SENTINELA • EVENTOS",
            icon_url=(
                "https://cdn.discordapp.com/emojis/"
                "1558683706489708634.webp"
            )
        )

        await canal.send(embed=embed)

    except discord.Forbidden:
        await ctx.send(
            "❌ O bot não tem permissão para publicar nesse canal."
        )

    except discord.HTTPException as erro:
        print(f"[ERRO PUBLICAR PASSE] {erro!r}")
        await ctx.send(
            "❌ Falha ao publicar. Confira os logs do Railway."
        )


@publicarpasse.error
async def publicarpasse_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ Você precisa ser administrador para publicar."
        )
    else:
        print(f"[ERRO COMANDO PASSE] {error!r}")


# ==========================================
# EVENTOS DE MEMBROS
# ==========================================

@bot.event
async def on_member_join(membro):
    cargo_recruta = discord.utils.get(
        membro.guild.roles,
        name=CARGO_RECRUTA
    )

    if cargo_recruta is None:
        print(
            f"[RECRUTAMENTO] Cargo não encontrado: "
            f"{CARGO_RECRUTA}"
        )
        return

    try:
        await membro.add_roles(
            cargo_recruta,
            reason="Novo membro entrou no servidor."
        )

        print(
            f"[RECRUTAMENTO] Cargo de recruta dado para {membro}."
        )

        await criar_recrutamento(membro)

    except discord.Forbidden:
        print(
            "[RECRUTAMENTO] Sem permissão para dar o cargo. "
            "Confira Gerenciar cargos e a hierarquia do bot."
        )

    except discord.HTTPException as erro:
        print(f"[ERRO AO RECEBER NOVO MEMBRO] {erro}")


@bot.event
async def on_member_update(before, after):
    cargo_recruta = discord.utils.get(
        after.guild.roles,
        name=CARGO_RECRUTA
    )

    cargo_membro = discord.utils.get(
        after.guild.roles,
        name=CARGO_MEMBRO
    )

    recebeu_recruta = (
        cargo_recruta is not None
        and cargo_recruta not in before.roles
        and cargo_recruta in after.roles
    )

    recebeu_membro = (
        cargo_membro is not None
        and cargo_membro not in before.roles
        and cargo_membro in after.roles
    )

    if recebeu_recruta:
        await criar_recrutamento(after)

    if recebeu_membro:
        canal_boas_vindas = after.guild.get_channel(
            CANAL_BOAS_VINDAS_ID
        )

        canal_regras = after.guild.get_channel(
            CANAL_REGRAS_ID
        )

        mencao_regras = (
            canal_regras.mention
            if isinstance(canal_regras, discord.TextChannel)
            else f"<#{CANAL_REGRAS_ID}>"
        )

        if isinstance(canal_boas_vindas, discord.TextChannel):
            embed = discord.Embed(
                title="🦁 NOVO SENTINELA NA ÁREA!",
                description=(
                    f"Salve, {after.mention}! Seja muito bem-vindo "
                    "à família Sentinela!\n\n"
                    "Agora você faz parte da tropa. "
                    "Chegue junto, conheça a galera e participe "
                    "das atividades da guilda.\n\n"
                    f"📚 Dá uma conferida em {mencao_regras} "
                    "para conhecer as regras da nossa comunidade."
                ),
                color=discord.Color.gold()
            )

            embed.set_image(url=IMAGEM_BOAS_VINDAS)
            embed.set_footer(
                text="SENTINELA • JUNTOS SOMOS MAIS FORTES"
            )

            try:
                await canal_boas_vindas.send(embed=embed)
            except discord.HTTPException as erro:
                print(f"[ERRO BOAS-VINDAS] {erro}")


# ==========================================
# INICIALIZACAO
# ==========================================

@bot.event
async def on_ready():
    print(f"🦁 Sentinela conectado como {bot.user}")
    print("[SENTINELA] Bot pronto para receber interações.")


async def main():
    if not TOKEN:
        print(
            "ERRO: defina a variável de ambiente DISCORD_TOKEN."
        )
        return

    async with bot:
        bot.add_view(FilaView())
        bot.add_view(RecrutamentoView())
        bot.add_view(ConfirmarRecusaView())

        await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())
