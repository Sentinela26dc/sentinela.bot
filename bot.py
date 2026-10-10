


import os
import discord
from discord.ext import commands

# ==============================
# CONFIGURAÇÕES
# ==============================

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

IMAGEM_BOAS_VINDAS = (
    "https://i.pinimg.com/474x/cf/a8/ac/"
    "cfa8acf9d3323076c8f1a4c5071a36c6.jpg"
)

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

filas = {}
canais_squad = {}

# ==============================
# INICIALIZAÇÃO
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
# FUNÇÕES DE RECRUTAMENTO
# ==============================

def eh_recrutador(interaction):
    if interaction.guild is None:
        return False

    if not isinstance(interaction.user, discord.Member):
        return False

    # Administradores do servidor podem aprovar.
    if interaction.user.guild_permissions.administrator:
        return True

    # Moderadores/recrutadores autorizados pelos IDs.
    return any(
        cargo.id in CARGOS_RECRUTADORES
        for cargo in interaction.user.roles
    )


def obter_id_recrutado(canal):
    if not isinstance(canal, discord.TextChannel):
        return None

    if not canal.topic:
        return None

    marcador = "recrutamento_usuario:"

    if marcador not in canal.topic:
        return None

    try:
        texto_id = canal.topic.split(marcador, 1)[1]
        texto_id = texto_id.split()[0].strip("|")
        return int(texto_id)
    except (ValueError, IndexError):
        return None


def recrutamento_encerrado(canal):
    if not isinstance(canal, discord.TextChannel):
        return True

    topico = canal.topic or ""

    return (
        "STATUS: APROVADO" in topico
        or "STATUS: RECUSADO" in topico
    )


# ==============================
# CONFIRMAÇÃO DA RECUSA
# ==============================

class ConfirmarRecusaView(discord.ui.View):

    def __init__(self, recrutado_id):
        super().__init__(timeout=60)
        self.recrutado_id = recrutado_id

    @discord.ui.button(
        label="Confirmar recusa",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="sentinela_confirmar_recusa"
    )
    async def confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not eh_recrutador(interaction):
            await interaction.response.send_message(
                "❌ Somente ADM ou moderadores autorizados "
                "podem recusar recrutamentos.",
                ephemeral=True
            )
            return

        canal = interaction.channel
        guild = interaction.guild

        if guild is None or not isinstance(
            canal, discord.TextChannel
        ):
            await interaction.response.send_message(
                "Não consegui identificar o canal.",
                ephemeral=True
            )
            return

        if obter_id_recrutado(canal) != self.recrutado_id:
            await interaction.response.send_message(
                "❌ Este canal não corresponde ao recrutamento.",
                ephemeral=True
            )
            return

        if recrutamento_encerrado(canal):
            await interaction.response.send_message(
                "⚠️ Este recrutamento já foi encerrado.",
                ephemeral=True
            )
            return

        membro = guild.get_member(self.recrutado_id)

        if membro is None:
            try:
                membro = await guild.fetch_member(
                    self.recrutado_id
                )
            except discord.NotFound:
                membro = None
            except discord.HTTPException:
                membro = None

        cargo_recruta = discord.utils.get(
            guild.roles,
            name=CARGO_RECRUTA
        )

        if membro is not None and cargo_recruta is not None:
            try:
                if cargo_recruta in membro.roles:
                    await membro.remove_roles(
                        cargo_recruta,
                        reason=(
                            f"Recrutamento recusado por "
                            f"{interaction.user}"
                        )
                    )
            except discord.Forbidden:
                await interaction.response.send_message(
                    "❌ Não consigo retirar o cargo de recruta. "
                    "Confira as permissões e a hierarquia de cargos.",
                    ephemeral=True
                )
                return
            except discord.HTTPException as erro:
                print(f"Erro ao retirar cargo de recruta: {erro}")

                await interaction.response.send_message(
                    "❌ O Discord não permitiu alterar o cargo. "
                    "Tente novamente.",
                    ephemeral=True
                )
                return

        try:
            topico = canal.topic or ""
            await canal.edit(
                topic=f"{topico} | STATUS: RECUSADO"[:1024],
                reason="Recrutamento recusado."
            )

            # O recrutado deixa de ver o canal encerrado.
            if membro is not None:
                await canal.set_permissions(
                    membro,
                    view_channel=False,
                    send_messages=False,
                    read_message_history=False,
                    reason="Recrutamento encerrado."
                )

            await canal.send(
                "❌ **RECRUTAMENTO ENCERRADO**\n\n"
                "A equipe decidiu não seguir com este "
                "recrutamento neste momento."
            )

        except discord.Forbidden:
            print(
                "Sem permissão para encerrar o canal "
                "de recrutamento."
            )
        except discord.HTTPException as erro:
            print(f"Erro ao encerrar recrutamento: {erro}")

        await interaction.response.edit_message(
            content="❌ Recrutamento recusado e encerrado.",
            view=None
        )

    @discord.ui.button(
        label="Cancelar",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_cancelar_recusa"
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="A recusa foi cancelada.",
            view=None
        )


# ==============================
# BOTÕES DE APROVAÇÃO
# ==============================

class RecrutamentoView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Aprovar",
        emoji=discord.PartialEmoji(
            name="emoji_aprovar",
            id=1558331820985163817
        ),
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_aprovar_recrutamento"
    )
    async def aprovar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not eh_recrutador(interaction):
            await interaction.response.send_message(
                "❌ Você não tem permissão para aprovar "
                "este recrutamento.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        canal = interaction.channel

        if guild is None or not isinstance(
            canal, discord.TextChannel
        ):
            await interaction.response.send_message(
                "Não consegui identificar o servidor ou canal.",
                ephemeral=True
            )
            return

        recrutado_id = obter_id_recrutado(canal)

        if recrutado_id is None:
            await interaction.response.send_message(
                "❌ Este não parece ser um canal de recrutamento.",
                ephemeral=True
            )
            return

        if recrutamento_encerrado(canal):
            await interaction.response.send_message(
                "⚠️ Este recrutamento já foi encerrado.",
                ephemeral=True
            )
            return

        membro = guild.get_member(recrutado_id)

        if membro is None:
            try:
                membro = await guild.fetch_member(recrutado_id)
            except discord.NotFound:
                await interaction.response.send_message(
                    "❌ Este usuário não está mais no servidor.",
                    ephemeral=True
                )
                return
            except discord.HTTPException:
                await interaction.response.send_message(
                    "❌ Não consegui localizar o recrutado. "
                    "Tente novamente.",
                    ephemeral=True
                )
                return

        cargo_recruta = discord.utils.get(
            guild.roles,
            name=CARGO_RECRUTA
        )

        cargo_membro = discord.utils.get(
            guild.roles,
            name=CARGO_MEMBRO
        )

        if cargo_membro is None:
            await interaction.response.send_message(
                f"❌ Não encontrei o cargo `{CARGO_MEMBRO}`.",
                ephemeral=True
            )
            return

        if cargo_recruta is None:
            await interaction.response.send_message(
                f"❌ Não encontrei o cargo `{CARGO_RECRUTA}`.",
                ephemeral=True
            )
            return

        if cargo_membro in membro.roles:
            await interaction.response.send_message(
                "⚠️ Este usuário já é um Sentinela.",
                ephemeral=True
            )
            return

        try:
            # Primeiro adiciona o cargo de membro.
            # Isso aciona a mensagem de boas-vindas existente.
            await membro.add_roles(
                cargo_membro,
                reason=(
                    f"Recrutamento aprovado por "
                    f"{interaction.user}"
                )
            )

            # Depois remove o cargo de recruta.
            if cargo_recruta in membro.roles:
                await membro.remove_roles(
                    cargo_recruta,
                    reason="Recrutamento aprovado."
                )

        except discord.Forbidden:
            await interaction.response.send_message(
                "❌ Não consegui alterar os cargos. "
                "Verifique se o bot tem Gerenciar Cargos "
                "e se seu cargo está acima dos cargos envolvidos.",
                ephemeral=True
            )
            return

        except discord.HTTPException as erro:
            print(f"Erro ao aprovar recrutado: {erro}")

            await interaction.response.send_message(
                "❌ O Discord não permitiu concluir a aprovação. "
                "Confira os cargos do usuário antes de tentar "
                "novamente.",
                ephemeral=True
            )
            return

        try:
            topico = canal.topic or ""
            await canal.edit(
                topic=f"{topico} | STATUS: APROVADO"[:1024],
                reason="Recrutamento aprovado."
            )
        except discord.HTTPException as erro:
            print(f"Erro ao atualizar tópico do canal: {erro}")

        await canal.send(
            f"✅ **RECRUTAMENTO APROVADO!**\n\n"
            f"Parabéns, {membro.mention}! Agora você faz "
            "parte da **Sentinela**. 🦁💛\n"
            "A mensagem de boas-vindas será enviada "
            "pelo sistema de cargos."
        )

        await interaction.response.edit_message(
            content=(
                f"✅ Recrutamento de {membro.mention} "
                "aprovado com sucesso!"
            ),
            view=None
        )

    @discord.ui.button(
        label="Recusar",
        emoji="❌",
        style=discord.ButtonStyle.danger,
        custom_id="sentinela_recusar_recrutamento"
    )
    async def recusar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not eh_recrutador(interaction):
            await interaction.response.send_message(
                "❌ Você não tem permissão para recusar "
                "este recrutamento.",
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

        recrutado_id = obter_id_recrutado(canal)

        if recrutado_id is None:
            await interaction.response.send_message(
                "❌ Este não parece ser um canal de recrutamento.",
                ephemeral=True
            )
            return

        if recrutamento_encerrado(canal):
            await interaction.response.send_message(
                "⚠️ Este recrutamento já foi encerrado.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            "⚠️ **Tem certeza que deseja recusar este recrutado?**\n"
            "O cargo de recruta será retirado e o acesso ao "
            "canal será encerrado.",
            view=ConfirmarRecusaView(recrutado_id),
            ephemeral=True
        )


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
        )
    }

    bot_membro = guild.me

    if bot_membro is not None:
        permissoes[bot_membro] = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            read_message_history=True,
            manage_channels=True
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

    canal = await guild.create_text_channel(
        name="🔒・squad-sentinela",
        category=categoria,
        overwrites=permissoes,
        topic=(
            "Canal privado da equipe de Guerra de Guilda "
            "da Sentinela."
        )
    )

    mencoes = " ".join(
        f"<@{jogador_id}>" for jogador_id in jogadores
    )

    await canal.send(
        "⚔️ **SQUAD COMPLETO — GUERRA DE GUILDA!**\n\n"
        "Salve, equipe Sentinela! Os quatro jogadores estão reunidos.\n\n"
        f"👥 **Integrantes:**\n{mencoes}\n\n"
        "💛 Organizem a estratégia por aqui!"
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

        if len(jogadores) == LIMITE_FILA:
            try:
                categoria = None

                if isinstance(
                    interaction.channel,
                    discord.TextChannel
                ):
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
                    "Confira se o bot tem a permissão Gerenciar Canais.",
                    ephemeral=True
                )
                return

            except discord.HTTPException as erro:
                jogadores.remove(jogador_id)
                print(f"Erro ao criar canal do squad: {erro}")

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
                f"🏆 **Squad completo!** Canal privado: "
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

        canal_id = canais_squad.pop(guild_id, None)

        if canal_id is not None:
            canal = interaction.guild.get_channel(canal_id)

            if canal is not None:
                try:
                    await canal.delete(
                        reason="Um jogador saiu da fila."
                    )
                except discord.HTTPException as erro:
                    print(f"Erro ao excluir canal do squad: {erro}")

        await interaction.response.edit_message(
            embed=criar_embed_fila(guild_id),
            view=self
        )


# ==============================
# COMANDO FILA
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
        value="`!sentinela` — Informações do bot.",
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
bot.add_view(RecrutamentoView())


# ==============================
# RECRUTAMENTO E BOAS-VINDAS
# ==============================

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

    # --------------------------------
    # RECEBEU O CARGO DE RECRUTA
    # --------------------------------

    recebeu_recruta = (
        cargo_recruta is not None
        and cargo_recruta.id not in cargos_antes
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

            if not isinstance(
                categoria,
                discord.CategoryChannel
            ):
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
                        "Canal privado de recrutamento | "
                        f"{marcador}"
                    ),
                    reason=f"Recrutamento iniciado para {after}"
                )

                embed_recrutamento = discord.Embed(
                    title="🦁 𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 | 𝐑𝐄𝐂𝐑𝐔𝐓𝐀𝐌𝐄𝐍𝐓𝐎",
                    description=(
                        f"Salve, {after.mention}! Bem-vindo(a) "
                        "ao seu canal de recrutamento. 💛\n\n"
                        "A equipe vai conversar com você por aqui.\n\n"
                        "Aguardem a avaliação de um ADM ou "
                        "moderador para concluir o recrutamento."
                    ),
                    color=discord.Color.gold()
                )

                await canal.send(
                    embed=embed_recrutamento,
                    view=RecrutamentoView()
                )

            except discord.Forbidden:
                print(
                    f"Sem permissão para criar canal de recrutamento "
                    f"para {after}."
                )

            except discord.HTTPException as erro:
                print(f"Erro no recrutamento: {erro}")

    # --------------------------------
    # RECEBEU O CARGO SENTINELA
    # ENVIA A MENSAGEM DE BOAS-VINDAS
    # --------------------------------

    recebeu_cargo_membro = (
        cargo_membro is not None
        and cargo_membro.id not in cargos_antes
        and cargo_membro.id in cargos_depois
    )

    if recebeu_cargo_membro:
        canal_boas_vindas = after.guild.get_channel(
            CANAL_BOAS_VINDAS_ID
        )

        if isinstance(
            canal_boas_vindas,
            discord.TextChannel
        ):
            embed = discord.Embed(
                title="🟡 NOVO SENTINELA NA ÁREA! 🦁",
                description=(
                    "Seja bem-vindo ao servidor! 🦁 🔥 "
                    f"{after.mention}\n\n"
                    "Agora você faz parte da **Sentinela**. "
                    "Fica à vontade pra resenhar com os sentinelas, "
                    "formar seu squad e participar das Guerras "
                    "de Guilda com a gente! 🦁\n\n"
                    "📚 Dá uma conferida nas regras do servidor "
                    "pra ficar por dentro da nossa comunidade "
                    "e evitar problemas."
                ),
                color=discord.Color.gold()
            )

            embed.set_image(url=IMAGEM_BOAS_VINDAS)

            try:
                await canal_boas_vindas.send(
                    content=after.mention,
                    embed=embed
                )

                print(
                    f"Boas-vindas enviadas para {after} "
                    "após receber o cargo Sentinela."
                )

            except discord.Forbidden:
                print(
                    "Sem permissão para enviar boas-vindas. "
                    "Confira as permissões do canal."
                )

            except discord.HTTPException as erro:
                print(f"Erro ao enviar boas-vindas: {erro}")

    if cargo_recruta is None:
        print(
            f"Cargo de recruta não encontrado: {CARGO_RECRUTA}"
        )

    if cargo_membro is None:
        print(
            f"Cargo Sentinela não encontrado: {CARGO_MEMBRO}"
        )


# ==============================
# BOT ONLINE
# ==============================

@bot.event
async def on_ready():
    print("=" * 40)
    print("🦁 SENTINELA BOT ONLINE")
    print(f"Conectado como: {bot.user}")
    print(f"ID: {bot.user.id}")
    print("=" * 40)
    print("Use !fila para criar a fila de guerra.")
    print("Aprovação de recrutamento ativada.")
    print("Boas-vindas serão enviadas ao receber o cargo Sentinela.")


if not TOKEN:
    raise RuntimeError(
        "Token não encontrado! Configure DISCORD_TOKEN no Railway."
    )

bot.run(TOKEN)
