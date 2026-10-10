
import os
import asyncio
import discord
from discord.ext import commands

# ========================================
# CONFIGURAÇÕES
# ========================================

TOKEN = os.getenv("DISCORD_TOKEN")

LIMITE_FILA = 4
TEMPO_EXCLUSAO_CANAL = 5

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

# Emoji comum para aprovação do recrutamento
EMOJI_APROVAR = "✅"

EMOJI_SENTINELA_URL = (
    "https://cdn.discordapp.com/emojis/"
    "1557941358990200852.png"
)

filas = {}
canais_squad = {}


# ========================================
# INICIALIZAÇÃO
# ========================================

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


def eh_recrutador(interaction):
    if interaction.guild is None:
        return False

    if not isinstance(interaction.user, discord.Member):
        return False

    if interaction.user.guild_permissions.administrator:
        return True

    return any(
        cargo.id in CARGOS_RECRUTADORES
        for cargo in interaction.user.roles
    )


def obter_id_recrutado(canal):
    if not isinstance(canal, discord.TextChannel):
        return None

    topico = canal.topic or ""
    marcador = "recrutamento_usuario:"

    if marcador not in topico:
        return None

    try:
        texto_id = topico.split(marcador, 1)[1]
        texto_id = texto_id.split()[0].strip("|")
        return int(texto_id)
    except (ValueError, IndexError):
        return None


def recrutamento_encerrado(canal):
    topico = canal.topic or ""

    return (
        "STATUS: APROVADO" in topico
        or "STATUS: RECUSADO" in topico
    )


async def excluir_canal_recrutamento(canal):
    await asyncio.sleep(TEMPO_EXCLUSAO_CANAL)

    try:
        await canal.delete(
            reason="Recrutamento encerrado."
        )
    except discord.NotFound:
        pass
    except discord.Forbidden:
        print("[RECRUTAMENTO] Sem permissão para excluir o canal.")
    except discord.HTTPException as erro:
        print(f"[RECRUTAMENTO] Erro ao excluir canal: {erro}")


# ========================================
# CONFIRMAÇÃO DA RECUSA
# ========================================

class ConfirmarRecusaView(discord.ui.View):

    def __init__(self, recrutado_id):
        super().__init__(timeout=60)
        self.recrutado_id = recrutado_id

    @discord.ui.button(
        label="Confirmar recusa",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_confirmar_recusa"
    )
    async def confirmar(self, interaction, button):
        if not eh_recrutador(interaction):
            await interaction.response.send_message(
                "❌ Você não tem permissão para isso.",
                ephemeral=True
            )
            return

        canal = interaction.channel
        guild = interaction.guild

        if guild is None or not isinstance(canal, discord.TextChannel):
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

        await interaction.response.defer()

        membro = guild.get_member(self.recrutado_id)

        if membro is None:
            try:
                membro = await guild.fetch_member(self.recrutado_id)
            except (discord.NotFound, discord.HTTPException):
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
                        reason=f"Recrutamento recusado por {interaction.user}"
                    )
            except discord.Forbidden:
                await interaction.followup.send(
                    "❌ Não consigo retirar o cargo. Confira as permissões "
                    "e a hierarquia de cargos do bot.",
                    ephemeral=True
                )
                return
            except discord.HTTPException as erro:
                print(f"[RECRUTAMENTO] Erro ao retirar cargo: {erro}")
                await interaction.followup.send(
                    "❌ Não consegui alterar o cargo.",
                    ephemeral=True
                )
                return

        try:
            await canal.edit(
                topic=f"{canal.topic or ''} | STATUS: RECUSADO"[:1024],
                reason="Recrutamento recusado."
            )

            if membro is not None:
                await canal.set_permissions(
                    membro,
                    view_channel=False,
                    send_messages=False,
                    read_message_history=False
                )

            await canal.send(
                "❌ **RECRUTAMENTO ENCERRADO**\n\n"
                "A equipe decidiu não seguir com este recrutamento "
                "neste momento.\n\n"
                f"Este canal será excluído em {TEMPO_EXCLUSAO_CANAL} segundos."
            )

        except discord.Forbidden:
            print("[RECRUTAMENTO] Sem permissão para encerrar o canal.")
        except discord.HTTPException as erro:
            print(f"[RECRUTAMENTO] Erro ao encerrar canal: {erro}")

        await interaction.edit_original_response(
            content="❌ Recrutamento recusado. O canal será excluído em breve.",
            view=None
        )

        await excluir_canal_recrutamento(canal)

    @discord.ui.button(
        label="Cancelar",
        emoji="↩️",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_cancelar_recusa"
    )
    async def cancelar(self, interaction, button):
        if not eh_recrutador(interaction):
            await interaction.response.send_message(
                "❌ Você não tem permissão para isso.",
                ephemeral=True
            )
            return

        await interaction.response.edit_message(
            content="A recusa foi cancelada.",
            view=None
        )


# ========================================
# BOTÕES DE RECRUTAMENTO
# ========================================

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
        if not eh_recrutador(interaction):
            await interaction.response.send_message(
                "❌ Você não tem permissão para aprovar.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        canal = interaction.channel

        if guild is None or not isinstance(canal, discord.TextChannel):
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
                    "❌ Não consegui localizar o usuário.",
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

        if cargo_recruta is None or cargo_membro is None:
            await interaction.response.send_message(
                "❌ Não encontrei os cargos de recruta ou Sentinela. "
                "Confira os nomes nas configurações.",
                ephemeral=True
            )
            return

        if cargo_membro in membro.roles:
            await interaction.response.send_message(
                "⚠️ Este usuário já é um Sentinela.",
                ephemeral=True
            )
            return

        await interaction.response.defer()

        try:
            await membro.add_roles(
                cargo_membro,
                reason=f"Recrutamento aprovado por {interaction.user}"
            )

            if cargo_recruta in membro.roles:
                await membro.remove_roles(
                    cargo_recruta,
                    reason="Recrutamento aprovado."
                )

        except discord.Forbidden:
            await interaction.followup.send(
                "❌ Não consegui alterar os cargos. Confira se o bot tem "
                "Gerenciar Cargos e se seu cargo está acima dos cargos envolvidos.",
                ephemeral=True
            )
            return
        except discord.HTTPException as erro:
            print(f"[RECRUTAMENTO] Erro ao aprovar: {erro}")
            await interaction.followup.send(
                "❌ O Discord não permitiu concluir a aprovação.",
                ephemeral=True
            )
            return

        try:
            await canal.edit(
                topic=f"{canal.topic or ''} | STATUS: APROVADO"[:1024],
                reason="Recrutamento aprovado."
            )

            await canal.send(
                "✅ **RECRUTAMENTO APROVADO!**\n\n"
                f"Parabéns, {membro.mention}! Agora você faz parte "
                "da **Sentinela**. 🦁💛\n\n"
                f"Este canal será excluído em {TEMPO_EXCLUSAO_CANAL} segundos."
            )

        except discord.HTTPException as erro:
            print(f"[RECRUTAMENTO] Erro ao finalizar aprovação: {erro}")

        await interaction.edit_original_response(
            content=f"✅ Recrutamento de {membro.mention} aprovado!",
            view=None
        )

        await excluir_canal_recrutamento(canal)

    @discord.ui.button(
        label="Recusar",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_recusar_recrutamento"
    )
    async def recusar(self, interaction, button):
        if not eh_recrutador(interaction):
            await interaction.response.send_message(
                "❌ Você não tem permissão para recusar.",
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
            "O cargo será retirado e o acesso ao canal será encerrado.",
            view=ConfirmarRecusaView(recrutado_id),
            ephemeral=True
        )


# ========================================
# CRIAÇÃO DA MENSAGEM DE RECRUTAMENTO
# ========================================

TITULO_RECRUTAMENTO = "🦁 𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 | 𝐑𝐄𝐂𝐑𝐔𝐓𝐀𝐌𝐄𝐍𝐓𝐎"


async def garantir_mensagem_recrutamento(canal, membro):
    embed = discord.Embed(
        title=TITULO_RECRUTAMENTO,
        description=(
            f"Salve, {membro.mention}! Bem-vindo(a) ao seu canal "
            "de recrutamento. 💛\n\n"
            "A equipe vai conversar com você por aqui.\n\n"
            "Aguarde a avaliação de um ADM ou moderador para concluir "
            "o recrutamento."
        ),
        color=discord.Color.gold()
    )

    try:
        mensagens = [
            mensagem async for mensagem in
            canal.history(limit=30, oldest_first=True)
        ]

        mensagem_recrutamento = discord.utils.find(
            lambda mensagem: (
                mensagem.author.id == bot.user.id
                and mensagem.embeds
                and mensagem.embeds[0].title == TITULO_RECRUTAMENTO
            ),
            mensagens
        )

        if mensagem_recrutamento is None:
            mensagem_recrutamento = await canal.send(embed=embed)

        # Os botões usam emojis comuns; não precisa de fallback.
        await mensagem_recrutamento.edit(
            view=RecrutamentoView()
        )

        print("[RECRUTAMENTO] Mensagem e botões carregados.")

    except discord.Forbidden:
        print(
            "[RECRUTAMENTO] Sem permissão para ver o histórico "
            "ou enviar mensagens."
        )
    except discord.HTTPException as erro:
        print(f"[RECRUTAMENTO] Erro na mensagem ou nos botões: {erro}")


# ========================================
# EMBED DA FILA — MANTIDO COMO ESTAVA
# ========================================

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
            for numero, jogador_id in enumerate(jogadores, start=1)
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


# ========================================
# CANAL PRIVADO DO SQUAD — MANTIDO
# ========================================

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
            embed_links=True,
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
        topic="Canal privado da equipe de Guerra de Guilda da Sentinela."
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


# ========================================
# BOTÕES DA FILA — MANTIDOS
# ========================================

class FilaView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="ENTRAR NA FILA",
        emoji=EMOJI_ENTRAR,
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_fila_entrar"
    )
    async def entrar(self, interaction, button):
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
        canal_criado = None

        if len(jogadores) == LIMITE_FILA:
            try:
                categoria = (
                    interaction.channel.category
                    if isinstance(interaction.channel, discord.TextChannel)
                    else None
                )

                canal_criado = await criar_canal_squad(
                    guild,
                    jogadores.copy(),
                    categoria
                )

                canais_squad[guild.id] = canal_criado.id

            except (discord.Forbidden, discord.HTTPException) as erro:
                jogadores.remove(jogador_id)
                print(f"[FILA] Erro ao criar canal do squad: {erro}")

                await interaction.response.edit_message(
                    embed=criar_embed_fila(guild.id),
                    view=self
                )

                await interaction.followup.send(
                    "❌ Não consegui criar o canal privado. "
                    "Confira a permissão Gerenciar Canais.",
                    ephemeral=True
                )
                return

        await interaction.response.edit_message(
            embed=criar_embed_fila(guild.id),
            view=self
        )

        if canal_criado is not None:
            await interaction.followup.send(
                f"🏆 **Squad completo!** Canal privado: {canal_criado.mention}",
                ephemeral=True
            )

    @discord.ui.button(
        label="SAIR DA FILA",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_fila_sair"
    )
    async def sair(self, interaction, button):
        if interaction.guild is None:
            await interaction.response.send_message(
                "Este botão só funciona dentro do servidor.",
                ephemeral=True
            )
            return

        guild = interaction.guild
        jogadores = obter_fila(guild.id)
        jogador_id = interaction.user.id

        if jogador_id not in jogadores:
            await interaction.response.send_message(
                "⚠️ Você não está na fila!",
                ephemeral=True
            )
            return

        jogadores.remove(jogador_id)

        canal_id = canais_squad.pop(guild.id, None)

        if canal_id is not None:
            canal = guild.get_channel(canal_id)

            if canal is not None:
                try:
                    await canal.delete(
                        reason="Um jogador saiu da fila."
                    )
                except discord.HTTPException as erro:
                    print(f"[FILA] Erro ao excluir canal do squad: {erro}")

        await interaction.response.edit_message(
            embed=criar_embed_fila(guild.id),
            view=self
        )


# ========================================
# COMANDOS — MANTIDOS
# ========================================

@bot.command(name="fila")
@commands.guild_only()
async def fila(ctx):
    await ctx.send(
        embed=criar_embed_fila(ctx.guild.id),
        view=FilaView()
    )


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
            "🔒 Canal privado automático para o squad\n"
            "🔰 Recrutamento com aprovação\n"
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
        value="`!sentinela` — Informações do bot.",
        inline=False
    )

    embed.add_field(
        name="⚔️ Guerra de Guilda",
        value="`!fila` — Publica o painel da fila.",
        inline=False
    )

    await ctx.send(embed=embed)


# ========================================
# REGISTRO DOS BOTÕES PERSISTENTES
# ========================================

bot.add_view(FilaView())
bot.add_view(RecrutamentoView())


# ========================================
# RECRUTAMENTO E BOAS-VINDAS
# ========================================

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

    recebeu_recruta = (
        cargo_recruta is not None
        and cargo_recruta.id not in cargos_antes
        and cargo_recruta.id in cargos_depois
    )

    if recebeu_recruta:
        marcador = f"recrutamento_usuario:{after.id}"

        canal = discord.utils.find(
            lambda c: (
                isinstance(c, discord.TextChannel)
                and c.topic
                and marcador in c.topic
            ),
            after.guild.channels
        )

        if canal is None:
            permissoes = {
                after.guild.default_role:
                    discord.PermissionOverwrite(
                        view_channel=False
                    ),
                after:
                    discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        attach_files=True,
                        embed_links=True
                    )
            }

            bot_membro = after.guild.me

            if bot_membro is not None:
                permissoes[bot_membro] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    embed_links=True,
                    manage_channels=True,
                    manage_messages=True
                )

            for cargo_id in CARGOS_RECRUTADORES:
                cargo = after.guild.get_role(cargo_id)

                if cargo is not None:
                    permissoes[cargo] = discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        embed_links=True,
                        manage_messages=True
                    )

            categoria = after.guild.get_channel(
                CATEGORIA_RECRUTAMENTO_ID
            )

            if not isinstance(categoria, discord.CategoryChannel):
                categoria = None

            nome_seguro = "".join(
                caractere
                if caractere.isalnum() or caractere in "-_"
                else "-"
                for caractere in after.display_name.lower()
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

                print(f"[RECRUTAMENTO] Canal criado: {canal.name}")

            except (discord.Forbidden, discord.HTTPException) as erro:
                print(f"[RECRUTAMENTO] Erro ao criar canal: {erro}")
                canal = None

        if canal is not None:
            if recrutamento_encerrado(canal):
                print(
                    "[RECRUTAMENTO] O canal existente já está encerrado."
                )
            else:
                await garantir_mensagem_recrutamento(canal, after)

    recebeu_cargo_membro = (
        cargo_membro is not None
        and cargo_membro.id not in cargos_antes
        and cargo_membro.id in cargos_depois
    )

    if recebeu_cargo_membro:
        canal_boas_vindas = after.guild.get_channel(
            CANAL_BOAS_VINDAS_ID
        )

        if isinstance(canal_boas_vindas, discord.TextChannel):
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
                    "pra ficar por dentro da nossa comunidade."
                ),
                color=discord.Color.gold()
            )

            embed.set_image(url=IMAGEM_BOAS_VINDAS)

            try:
                await canal_boas_vindas.send(
                    content=after.mention,
                    embed=embed
                )
                print(f"[BOAS-VINDAS] Mensagem enviada para {after}.")

            except discord.Forbidden:
                print("[BOAS-VINDAS] Sem permissão para enviar mensagem.")
            except discord.HTTPException as erro:
                print(f"[BOAS-VINDAS] Erro ao enviar boas-vindas: {erro}")

    if cargo_recruta is None:
        print(f"[CONFIG] Cargo não encontrado: {CARGO_RECRUTA}")

    if cargo_membro is None:
        print(f"[CONFIG] Cargo não encontrado: {CARGO_MEMBRO}")


# ========================================
# BOT ONLINE
# ========================================

@bot.event
async def on_ready():
    print("=" * 40)
    print("SENTINELA BOT ONLINE")
    print(f"Conectado como: {bot.user}")
    print(f"ID: {bot.user.id}")
    print("=" * 40)
    print("Use !fila para criar a fila de guerra.")
    print("Recrutamento e boas-vindas carregados.")


if not TOKEN:
    raise RuntimeError(
        "Token não encontrado! Configure DISCORD_TOKEN no Railway."
    )

bot.run(TOKEN)
