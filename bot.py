
import os
import asyncio
import discord
from discord.ext import commands

# ==========================================
# CONFIGURAÇÕES
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
    "https://cdn.discordapp.com/emojis/1557941358990200852.png"
)

# ==========================================
# DISCORD
# ==========================================

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)

filas = {}
canais_squad = {}
mensagens_fila = {}


# ==========================================
# FUNÇÕES AUXILIARES
# ==========================================

def obter_fila(guild_id):
    if guild_id not in filas:
        filas[guild_id] = []
    return filas[guild_id]


def eh_recrutador(membro):
    if membro.guild_permissions.administrator:
        return True

    cargos_autorizados = {
        CARGO_MODERADOR_ID,
        CARGO_ADM_ID
    }

    return any(
        cargo.id in cargos_autorizados
        for cargo in membro.roles
    )


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
        await canal.delete(
            reason="Recrutamento encerrado."
        )
    except (discord.NotFound, discord.Forbidden):
        pass


# ==========================================
# RECRUTAMENTO: RECUSA
# ==========================================

class ConfirmarRecusaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Confirmar recusa",
        style=discord.ButtonStyle.danger,
        custom_id="sentinela_confirmar_recusa"
    )
    async def confirmar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not eh_recrutador(interaction.user):
            await interaction.response.send_message(
                "❌ Você não tem permissão para fazer isso.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
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

        membro = interaction.guild.get_member(recrutado_id)

        if membro:
            cargo_recruta = discord.utils.get(
                interaction.guild.roles,
                name=CARGO_RECRUTA
            )

            if cargo_recruta and cargo_recruta in membro.roles:
                try:
                    await membro.remove_roles(
                        cargo_recruta,
                        reason="Recrutamento recusado."
                    )
                except discord.Forbidden:
                    pass

        try:
            await canal.edit(
                topic=(
                    f"recrutamento_usuario:{recrutado_id} "
                    "STATUS: RECUSADO"
                )
            )
        except discord.Forbidden:
            pass

        await interaction.response.edit_message(
            content="❌ **RECRUTAMENTO RECUSADO.**",
            view=None
        )

        await canal.send(
            "Este recrutamento foi encerrado. "
            "O canal será excluído em alguns segundos."
        )

        await excluir_canal_recrutamento(canal)

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_cancelar_recusa"
    )
    async def cancelar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.edit_message(
            content="Recusa cancelada.",
            view=None
        )


# ==========================================
# RECRUTAMENTO: APROVAR OU RECUSAR
# ==========================================

class RecrutamentoView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Aprovar",
        emoji="✅",
        style=discord.ButtonStyle.success,
        custom_id="sentinela_aprovar_recrutamento"
    )
    async def aprovar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        if not eh_recrutador(interaction.user):
            await interaction.response.send_message(
                "❌ Você não tem permissão para aprovar recrutados.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
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

        membro = interaction.guild.get_member(recrutado_id)

        if membro is None:
            await interaction.response.send_message(
                "O recrutado não está mais no servidor.",
                ephemeral=True
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
            await interaction.response.send_message(
                f"Não encontrei o cargo `{CARGO_MEMBRO}`.",
                ephemeral=True
            )
            return

        try:
            await membro.add_roles(
                cargo_membro,
                reason="Recrutamento aprovado."
            )

            if cargo_recruta and cargo_recruta in membro.roles:
                await membro.remove_roles(
                    cargo_recruta,
                    reason="Recrutamento aprovado."
                )

        except discord.Forbidden:
            await interaction.response.send_message(
                "Não consegui alterar os cargos. "
                "Verifique as permissões e a posição do cargo do bot.",
                ephemeral=True
            )
            return

        try:
            await canal.edit(
                topic=(
                    f"recrutamento_usuario:{recrutado_id} "
                    "STATUS: APROVADO"
                )
            )
        except discord.Forbidden:
            pass

        await interaction.response.edit_message(
            content=f"✅ **{membro.mention} FOI APROVADO!**",
            view=None
        )

        await canal.send(
            f"🦁 Parabéns, {membro.mention}! "
            "Você agora faz parte da Sentinela!"
        )

        await excluir_canal_recrutamento(canal)

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
        if not eh_recrutador(interaction.user):
            await interaction.response.send_message(
                "❌ Você não tem permissão para recusar recrutados.",
                ephemeral=True
            )
            return

        canal = interaction.channel

        if not isinstance(canal, discord.TextChannel):
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
# MENSAGEM DO CANAL DE RECRUTAMENTO
# ==========================================

TITULO_RECRUTAMENTO = (
    "🦁 𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 | 𝐑𝐄𝐂𝐑𝐔𝐓𝐀𝐌𝐄𝐍𝐓𝐎"
)


async def garantir_mensagem_recrutamento(canal, membro):
    embed = discord.Embed(
        title=TITULO_RECRUTAMENTO,
        description=(
            f"Salve, {membro.mention}!\n\n"
            "Este é o seu canal de recrutamento na Sentinela.\n\n"
            "Aguarde um administrador ou moderador "
            "para avaliar seu recrutamento.\n\n"
            "🦁 Boa sorte!"
        ),
        color=discord.Color.gold()
    )

    embed.set_footer(
        text="SENTINELA • RECRUTAMENTO"
    )

    moderador = canal.guild.get_role(CARGO_MODERADOR_ID)
    adm = canal.guild.get_role(CARGO_ADM_ID)

    mencoes_equipe = " ".join(
        cargo.mention
        for cargo in (moderador, adm)
        if cargo is not None
    )

    # Se já existir uma mensagem do bot, atualiza.
    async for mensagem in canal.history(limit=20):
        if mensagem.author == bot.user and mensagem.embeds:
            await mensagem.edit(
                content=mencoes_equipe or None,
                embed=embed,
                view=RecrutamentoView(),
                allowed_mentions=discord.AllowedMentions(
                    roles=True,
                    users=True
                )
            )
            return

    # Mensagem nova com menção aos cargos.
    await canal.send(
        content=mencoes_equipe or None,
        embed=embed,
        view=RecrutamentoView(),
        allowed_mentions=discord.AllowedMentions(
            roles=True,
            users=True
        )
    )


# ==========================================
# FILA DA GUERRA DE GUILDA
# ==========================================

def criar_embed_fila(guild_id):
    fila = obter_fila(guild_id)

    embed = discord.Embed(
        title="𝐆𝐔𝐄𝐑𝐑𝐀 𝐃𝐄 𝐆𝐔𝐈𝐋𝐃𝐀",
        description=(
            "⚔️ **FORME SEU SQUAD E AMASSE GERAL NA GUERRA!**"
        ),
        color=discord.Color.gold()
    )

    embed.add_field(
        name=f"{EMOJI_SQUAD} JOGADORES NA FILA",
        value=f"**{len(fila)} / {LIMITE_FILA} jogadores**",
        inline=False
    )

    if fila:
        jogadores = "\n".join(
            f"**{i}.** <@{membro_id}>"
            for i, membro_id in enumerate(fila, start=1)
        )
    else:
        jogadores = "A fila está vazia. Entre e forme seu squad!"

    embed.add_field(
        name="👥 PARTICIPANTES",
        value=jogadores,
        inline=False
    )

    embed.set_footer(
        text="SENTINELA • GUERRA DE GUILDA"
    )

    embed.set_thumbnail(url=EMOJI_SENTINELA_URL)

    return embed


async def criar_canal_squad(guild, fila):
    categoria = None

    canal_anterior_id = canais_squad.get(guild.id)
    if canal_anterior_id:
        canal_anterior = guild.get_channel(canal_anterior_id)
        if canal_anterior:
            try:
                await canal_anterior.delete(
                    reason="Preparando um novo squad."
                )
            except discord.HTTPException:
                pass

    permissoes = {
        guild.default_role: discord.PermissionOverwrite(
            view_channel=False
        )
    }

    for membro_id in fila:
        membro = guild.get_member(membro_id)
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

    bot_membro = guild.me
    if bot_membro:
        permissoes[bot_membro] = discord.PermissionOverwrite(
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

    mencoes = " ".join(
        f"<@{membro_id}>"
        for membro_id in fila
    )

    await canal.send(
        f"🦁 **SQUAD COMPLETO!**\n\n"
        f"{mencoes}\n\n"
        "Organizem-se para a Guerra de Guilda e boa sorte!"
    )

    return canal


class FilaView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="ENTRAR NA FILA",
        emoji=EMOJI_ENTRAR,
        style=discord.ButtonStyle.primary,
        custom_id="sentinela_entrar_fila"
    )
    async def entrar(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild

        if guild is None:
            return

        fila = obter_fila(guild.id)
        membro_id = interaction.user.id

        if membro_id in fila:
            await interaction.response.send_message(
                "Você já está na fila!",
                ephemeral=True
            )
            return

        if len(fila) >= LIMITE_FILA:
            await interaction.response.send_message(
                "A fila já está completa!",
                ephemeral=True
            )
            return

        fila.append(membro_id)

        await interaction.response.edit_message(
            embed=criar_embed_fila(guild.id),
            view=self
        )

        if len(fila) == LIMITE_FILA:
            try:
                canal = await criar_canal_squad(guild, list(fila))
                await canal.send(
                    "A fila foi fechada porque o squad está completo."
                )
            except discord.Forbidden:
                await interaction.followup.send(
                    "Não consegui criar o canal privado. "
                    "Verifique se o bot pode gerenciar canais.",
                    ephemeral=True
                )

    @discord.ui.button(
        label="SAIR DA FILA",
        emoji="❌",
        style=discord.ButtonStyle.secondary,
        custom_id="sentinela_sair_fila"
    )
    async def sair(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        guild = interaction.guild

        if guild is None:
            return

        fila = obter_fila(guild.id)
        membro_id = interaction.user.id

        if membro_id not in fila:
            await interaction.response.send_message(
                "Você não está na fila.",
                ephemeral=True
            )
            return

        fila.remove(membro_id)

        # Se um jogador sair de um squad completo,
        # o canal privado daquele squad será excluído.
        canal_id = canais_squad.pop(guild.id, None)

        if canal_id:
            canal = guild.get_channel(canal_id)
            if canal:
                try:
                    await canal.delete(
                        reason="Um jogador saiu da fila."
                    )
                except discord.HTTPException:
                    pass

        await interaction.response.edit_message(
            embed=criar_embed_fila(guild.id),
            view=self
        )


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
        "`!fila` — publica a fila da Guerra de Guilda"
    )


@bot.command()
@commands.has_permissions(manage_guild=True)
async def fila(ctx):
    mensagem = await ctx.send(
        embed=criar_embed_fila(ctx.guild.id),
        view=FilaView()
    )

    mensagens_fila[ctx.guild.id] = mensagem.id


@fila.error
async def fila_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send(
            "❌ Você precisa da permissão **Gerenciar servidor** "
            "para publicar a fila."
        )


# ==========================================
# EVENTOS DE MEMBROS
# ==========================================

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

    recebeu_cargo_recruta = (
        cargo_recruta is not None
        and cargo_recruta not in before.roles
        and cargo_recruta in after.roles
    )

    recebeu_cargo_membro = (
        cargo_membro is not None
        and cargo_membro not in before.roles
        and cargo_membro in after.roles
    )

    # Cria canal privado quando alguém recebe o cargo de recruta.
    if recebeu_cargo_recruta:
        categoria = after.guild.get_channel(
            CATEGORIA_RECRUTAMENTO_ID
        )

        permissoes = {
            after.guild.default_role:
                discord.PermissionOverwrite(
                    view_channel=False
                ),
            after:
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )
        }

        for cargo_id in (
            CARGO_MODERADOR_ID,
            CARGO_ADM_ID
        ):
            cargo = after.guild.get_role(cargo_id)

            if cargo:
                permissoes[cargo] = discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True
                )

        if after.guild.me:
            permissoes[after.guild.me] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True
                )
            )

        nome_canal = f"recrutamento-{after.name}".lower()
        nome_canal = nome_canal.replace(" ", "-")[:90]

        try:
            canal = await after.guild.create_text_channel(
                name=nome_canal,
                category=(
                    categoria
                    if isinstance(categoria, discord.CategoryChannel)
                    else None
                ),
                overwrites=permissoes,
                topic=f"recrutamento_usuario:{after.id}",
                reason="Novo recrutamento Sentinela."
            )

            await garantir_mensagem_recrutamento(
                canal,
                after
            )

        except discord.Forbidden:
            print(
                "Sem permissão para criar o canal de recrutamento."
            )

    # Mensagem de boas-vindas quando recebe o cargo de membro.
    if recebeu_cargo_membro:
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
                    f"📚 Dá uma conferida no canal de "
                    f"{mencao_regras} para conhecer as regras "
                    "da nossa comunidade."
                ),
                color=discord.Color.gold()
            )

            embed.set_image(url=IMAGEM_BOAS_VINDAS)
            embed.set_footer(
                text="SENTINELA • JUNTOS SOMOS MAIS FORTES"
            )

            await canal_boas_vindas.send(embed=embed)


# ==========================================
# INICIALIZAÇÃO
# ==========================================

@bot.event
async def on_ready():
    print(f"🦁 Sentinela conectado como {bot.user}")


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
