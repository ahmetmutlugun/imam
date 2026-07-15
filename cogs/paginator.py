import discord


class EmbedPaginator(discord.ui.View):
    def __init__(self, pages: list, user_id: int, timeout: float = 3600):
        super().__init__(timeout=timeout)
        self.pages = pages
        self.current = 0
        self.user_id = user_id
        self.message = None
        self._update_buttons()

    def _update_buttons(self):
        at_start = self.current == 0
        at_end = self.current == len(self.pages) - 1
        self.first_button.disabled = at_start
        self.prev_button.disabled = at_start
        self.next_button.disabled = at_end
        self.last_button.disabled = at_end
        self.counter_button.label = f"{self.current + 1}/{len(self.pages)}"

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label='⏮', style=discord.ButtonStyle.secondary)
    async def first_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = 0
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label='◀', style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label='1/1', style=discord.ButtonStyle.secondary, disabled=True)
    async def counter_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        pass

    @discord.ui.button(label='▶', style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label='⏭', style=discord.ButtonStyle.secondary)
    async def last_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current = len(self.pages) - 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                # The interaction webhook token expires after 15 minutes, so
                # this edit fails with 50027 once the view outlives the token.
                pass

    async def send(self, interaction: discord.Interaction, deferred: bool = False):
        self._update_buttons()
        if deferred:
            self.message = await interaction.followup.send(embed=self.pages[0], view=self, wait=True)
        else:
            await interaction.response.send_message(embed=self.pages[0], view=self)
            self.message = await interaction.original_response()
