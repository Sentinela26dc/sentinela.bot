
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
                permissoes[bot_membro] = (
                    discord.PermissionOverwrite(
                        view_channel=True,
                        send_messages=True,
                        read_message_history=True,
                        embed_links=True,
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
                            embed_links=True,
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

                print(
                    f"[RECRUTAMENTO] Canal criado: {canal.name}"
                )

            except (discord.Forbidden, discord.HTTPException) as erro:
                print(
                    f"[RECRUTAMENTO] Erro ao criar canal: "
                    f"{type(erro).__name__}: {erro}"
                )
                canal = None

        if canal is not None:
            try:
                embed_recrutamento = discord.Embed(
                    title=(
                        "🦁 𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 | "
                        "𝐑𝐄𝐂𝐑𝐔𝐓𝐀𝐌𝐄𝐍𝐓𝐎"
                    ),
                    description=(
                        f"Salve, {after.mention}! Bem-vindo(a) "
                        "ao seu canal de recrutamento. 💛\n\n"
                        "A equipe vai conversar com você por aqui.\n\n"
                        "Aguarde a avaliação de um ADM ou "
                        "moderador para concluir o recrutamento."
                    ),
                    color=discord.Color.gold()
                )

                # Envia a mensagem primeiro, sem os botões.
                mensagens = [
                    mensagem async for mensagem in
                    canal.history(limit=10, oldest_first=True)
                ]

                mensagem_recrutamento = discord.utils.find(
                    lambda m: (
                        m.author.id == bot.user.id
                        and m.embeds
                        and m.embeds[0].title
                        == "🦁 𝐒𝐄𝐍𝐓𝐈𝐍𝐄𝐋𝐀 | 𝐑𝐄𝐂𝐑𝐔𝐓𝐀𝐌𝐄𝐍𝐓𝐎"
                    ),
                    mensagens
                )

                if mensagem_recrutamento is None:
                    mensagem_recrutamento = await canal.send(
                        embed=embed_recrutamento
                    )
                    print(
                        "[RECRUTAMENTO] Boas-vindas enviadas."
                    )

                # Tenta adicionar os botões com o emoji personalizado.
                try:
                    await mensagem_recrutamento.edit(
                        view=RecrutamentoView()
                    )
                    print(
                        "[RECRUTAMENTO] Botões enviados com sucesso."
                    )

                except (discord.HTTPException, ValueError, TypeError) as erro:
                    print(
                        "[RECRUTAMENTO] Falha com os botões "
                        f"originais: {type(erro).__name__}: {erro}"
                    )

                    # Mantém o emoji personalizado no código.
                    # Se ele for rejeitado pelo Discord, tenta novamente
                    # com o mesmo botão sem emoji para não perder a função.
                    view_fallback = RecrutamentoView()

                    for item in view_fallback.children:
                        if (
                            isinstance(item, discord.ui.Button)
                            and item.custom_id
                            == "sentinela_aprovar_recrutamento"
                        ):
                            item.emoji = None

                    try:
                        await mensagem_recrutamento.edit(
                            view=view_fallback
                        )
                        print(
                            "[RECRUTAMENTO] Botões enviados "
                            "com alternativa sem emoji."
                        )

                    except discord.HTTPException as erro_final:
                        print(
                            "[RECRUTAMENTO] Não foi possível "
                            "enviar os botões: "
                            f"{type(erro_final).__name__}: {erro_final}"
                        )

            except (discord.Forbidden, discord.HTTPException) as erro:
                print(
                    "[RECRUTAMENTO] Erro ao enviar a mensagem: "
                    f"{type(erro).__name__}: {erro}"
                )

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
                    f"[BOAS-VINDAS] Mensagem enviada para {after}."
                )

            except (discord.Forbidden, discord.HTTPException) as erro:
                print(
                    "[BOAS-VINDAS] Erro ao enviar mensagem: "
                    f"{type(erro).__name__}: {erro}"
                )
