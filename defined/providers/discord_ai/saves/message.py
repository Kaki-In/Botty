import typing as _T
import saves as _saves
import json as _json
import discord as _discord
import shutil as _shutil

class _discord_properties_file_object(_T.TypedDict):
    discord_message: _discord.Message
    message_type: str

class DiscordMessagePropertiesFile():
    def __init__(self, resource: _saves.ResourceFile) -> None:
        self.__resource = resource

    def read_message_id(self) -> int:
        """Lit uniquement le message_id sans reconstruire l'objet Message (pas de client requis)."""
        data = _json.loads(self.__resource.read_content())
        return data['message_id']

    def read_message_properties(self, client: _discord.Client) -> _discord_properties_file_object:
        data = _json.loads(self.__resource.read_content())

        channel = client.get_channel(data['channel_id'])
        assert channel is not None, f"Channel {data['channel_id']} introuvable dans le cache du client"

        message = _discord.Message(
            state=client._connection,
            channel=channel,           # type: ignore[arg-type]
            data=data['message_data']
        )

        return {
            'discord_message': message,
            'message_type': data['message_type']
        }

    def write_message_properties(self, message: _discord.Message, message_type: str) -> None:
        self.__resource.write_content(_json.dumps({
            'channel_id': message.channel.id,
            'guild_id': message.guild.id if message.guild else None,
            'message_id': message.id,
            'message_data': {
                'id': str(message.id),
                'channel_id': str(message.channel.id),
                'author': {
                    'id': str(message.author.id),
                    'username': message.author.name,
                    'discriminator': message.author.discriminator,
                    'global_name': message.author.global_name,
                    'avatar': str(message.author.avatar) if message.author.avatar else None,
                    'bot': message.author.bot,
                },
                'content': message.content,
                'timestamp': message.created_at.isoformat(),
                'edited_timestamp': message.edited_at.isoformat() if message.edited_at else None,
                'tts': message.tts,
                'mention_everyone': message.mention_everyone,
                'mentions': [{'id': str(u.id), 'username': u.name, 'discriminator': u.discriminator, 'avatar': str(u.avatar) if u.avatar else None, 'bot': u.bot} for u in message.mentions],
                'mention_roles': [str(r.id) for r in message.role_mentions],
                'attachments': [{'id': str(a.id), 'filename': a.filename, 'url': a.url, 'proxy_url': a.proxy_url, 'size': a.size, 'content_type': a.content_type} for a in message.attachments],
                'embeds': [e.to_dict() for e in message.embeds],
                'pinned': message.pinned,
                'type': message.type.value,
            },
            'message_type': message_type
        }, indent=2))

class DiscordMessageSaver():
    def __init__(self, directory: _saves.ResourcesDirectory) -> None:
        self.__directory = directory
        self.__properties_file = DiscordMessagePropertiesFile(directory.get_resource('properties.json'))
        self.__saves_directory = directory.get_directory('saves')

    @property
    def directory(self) -> _saves.ResourcesDirectory:
        return self.__directory

    @property
    def message_saves_directory(self) -> _saves.ResourcesDirectory:
        return self.__saves_directory

    @property
    def properties_file(self) -> DiscordMessagePropertiesFile:
        return self.__properties_file

    def delete(self) -> None:
        _shutil.rmtree(self.__directory.path)