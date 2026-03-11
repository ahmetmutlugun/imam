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
        self.prev_button.disabled = self.current == 0
        self.next_button.disabled = self.current == len(self.pages) - 1

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        return interaction.user.id == self.user_id

    @discord.ui.button(label='◀', style=discord.ButtonStyle.secondary)
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current -= 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    @discord.ui.button(label='▶', style=discord.ButtonStyle.secondary)
    async def next_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.current += 1
        self._update_buttons()
        await interaction.response.edit_message(embed=self.pages[self.current], view=self)

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.NotFound:
                pass

    async def send(self, interaction: discord.Interaction, deferred: bool = False):
        self._update_buttons()
        if deferred:
            self.message = await interaction.followup.send(embed=self.pages[0], view=self, wait=True)
        else:
            await interaction.response.send_message(embed=self.pages[0], view=self)
            self.message = await interaction.original_response()
