"""
Emoji Steganography App - Kivy Android Version
Two modes:
1. TAG MODE (Default) - Text hidden as invisible tag characters
2. BINARY MODE - Text encoded as binary using zero-width characters

Built with Kivy for Android deployment via Google Colab
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.togglebutton import ToggleButton
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.utils import platform

# =============================================================================
# TAG MODE: Full Unicode support
# =============================================================================
TAG_BASE = 0xE0000
TAG_END = 0xE007F

def text_to_tags(text):
    """Convert ANY text to invisible tag characters."""
    utf8_bytes = text.encode('utf-8')
    result = []
    for byte in utf8_bytes:
        high = (byte >> 4) & 0x0F
        low = byte & 0x0F
        result.append(chr(TAG_BASE + high))
        result.append(chr(TAG_BASE + low))
    return ''.join(result)

def tags_to_text(tags):
    """Convert tag characters back to visible text."""
    nibbles = []
    for char in tags:
        code = ord(char)
        if TAG_BASE <= code < TAG_BASE + 16:
            nibbles.append(code - TAG_BASE)
        elif code == TAG_END:
            break
    
    bytes_list = []
    for i in range(0, len(nibbles) - 1, 2):
        high = nibbles[i]
        low = nibbles[i + 1]
        bytes_list.append((high << 4) | low)
    
    try:
        return bytes(bytes_list).decode('utf-8')
    except:
        return None

def hide_text_in_emoji_tags(emoji, hidden_text):
    """Hide ANY text in emoji using tag characters."""
    tag_text = text_to_tags(hidden_text)
    return emoji + tag_text + chr(TAG_END)

def reveal_text_from_emoji_tags(stego_emoji):
    """Reveal hidden tag text from emoji."""
    nibbles = []
    for char in stego_emoji:
        code = ord(char)
        if TAG_BASE <= code < TAG_BASE + 16:
            nibbles.append(code - TAG_BASE)
        elif code == TAG_END:
            break
    
    if not nibbles:
        return None
    
    bytes_list = []
    for i in range(0, len(nibbles) - 1, 2):
        high = nibbles[i]
        low = nibbles[i + 1]
        bytes_list.append((high << 4) | low)
    
    try:
        return bytes(bytes_list).decode('utf-8')
    except:
        return None

# =============================================================================
# BINARY MODE: Text encoded as binary using zero-width characters
# =============================================================================
ZERO_WIDTH_CHARS = {
    '0': '\u200B',
    '1': '\u200C',
    'sep': '\u200D'
}

def text_to_binary(text):
    """Convert text to binary string using UTF-8 encoding."""
    utf8_bytes = text.encode('utf-8')
    return ''.join(format(byte, '08b') for byte in utf8_bytes)

def binary_to_text(binary):
    """Convert binary string to text."""
    bytes_list = []
    for i in range(0, len(binary), 8):
        byte = binary[i:i+8]
        if len(byte) == 8:
            bytes_list.append(int(byte, 2))
    
    if not bytes_list:
        return None
    
    raw_bytes = bytes(bytes_list)
    
    try:
        result = raw_bytes.decode('utf-8')
        control_count = sum(1 for c in result if ord(c) < 32 and c not in '\n\r\t')
        if control_count <= len(result) * 0.1:
            return result
    except UnicodeDecodeError:
        pass
    
    try:
        return raw_bytes.decode('latin-1')
    except:
        pass
    
    try:
        return ''.join(chr(b) for b in bytes_list)
    except:
        return None

def encode_text_in_emoji_binary(emoji, hidden_text):
    """Encode text as binary zero-width characters."""
    binary = text_to_binary(hidden_text)
    hidden_chars = [ZERO_WIDTH_CHARS[bit] for bit in binary]
    hidden_chars.append(ZERO_WIDTH_CHARS['sep'])
    return emoji + ''.join(hidden_chars)

def decode_text_from_emoji_binary(stego_emoji):
    """Decode binary hidden text from emoji."""
    binary = []
    for char in stego_emoji:
        if char == ZERO_WIDTH_CHARS['0']:
            binary.append('0')
        elif char == ZERO_WIDTH_CHARS['1']:
            binary.append('1')
        elif char == ZERO_WIDTH_CHARS['sep']:
            break
    
    if not binary:
        return None
    
    try:
        return binary_to_text(''.join(binary))
    except:
        return None


class StyledTextInput(TextInput):
    """Enhanced TextInput with better emoji support and context menu."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.multiline = kwargs.get('multiline', True)
        # Enable text selection and context menu (cut, copy, paste, select all)
        self.use_bubble = True
        self.use_handles = True


class EncodeTab(BoxLayout):
    """Encoding tab for hiding text in emojis."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        
        # Mode selection
        mode_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        mode_label = Label(text='[b]Encoding Mode:[/b]', markup=True, size_hint_x=0.4)
        self.tag_btn = ToggleButton(text='TAG', group='encode_mode', state='down', size_hint_x=0.3)
        self.binary_btn = ToggleButton(text='BINARY', group='encode_mode', size_hint_x=0.3)
        mode_layout.add_widget(mode_label)
        mode_layout.add_widget(self.tag_btn)
        mode_layout.add_widget(self.binary_btn)
        self.add_widget(mode_layout)
        
        # Emoji input
        self.add_widget(Label(text='[b]Enter Emoji:[/b]', markup=True, size_hint_y=None, height=30))
        self.emoji_input = StyledTextInput(
            hint_text='Paste or type emoji here (use Gboard 😊)',
            size_hint_y=None,
            height=80,
            multiline=False,
            font_size='24sp'
        )
        self.add_widget(self.emoji_input)
        
        # Hidden text input
        self.add_widget(Label(text='[b]Text to Hide:[/b]', markup=True, size_hint_y=None, height=30))
        self.hidden_input = StyledTextInput(
            hint_text='Enter secret message here...',
            size_hint_y=0.3,
            font_size='16sp'
        )
        self.add_widget(self.hidden_input)
        
        # Encode button
        encode_btn = Button(
            text='🔒 HIDE MESSAGE',
            size_hint_y=None,
            height=60,
            background_color=(0.05, 0.45, 0.47, 1),
            font_size='18sp',
            bold=True
        )
        encode_btn.bind(on_press=self.encode_message)
        self.add_widget(encode_btn)
        
        # Result output
        self.add_widget(Label(text='[b]Result:[/b]', markup=True, size_hint_y=None, height=30))
        self.result_output = StyledTextInput(
            readonly=True,
            size_hint_y=0.25,
            font_size='20sp',
            background_color=(0.15, 0.15, 0.15, 1),
            foreground_color=(1, 0.84, 0, 1)
        )
        self.add_widget(self.result_output)
        
        # Copy button
        copy_btn = Button(
            text='📋 COPY EMOJI',
            size_hint_y=None,
            height=50,
            background_color=(0, 1, 0.53, 1),
            color=(0.1, 0.1, 0.1, 1),
            font_size='16sp',
            bold=True
        )
        copy_btn.bind(on_press=self.copy_result)
        self.add_widget(copy_btn)
    
    def encode_message(self, instance):
        """Hide the message in the emoji."""
        emoji = self.emoji_input.text.strip()
        hidden_text = self.hidden_input.text.strip()
        
        if not emoji:
            self.show_popup('⚠ Input Required', 'Please enter an emoji!')
            return
        
        if not hidden_text:
            self.show_popup('⚠ Input Required', 'Please enter text to hide!')
            return
        
        try:
            if self.tag_btn.state == 'down':
                stego_emoji = hide_text_in_emoji_tags(emoji, hidden_text)
                mode_name = 'TAG'
            else:
                stego_emoji = encode_text_in_emoji_binary(emoji, hidden_text)
                mode_name = 'BINARY'
            
            self.result_output.text = stego_emoji
            
            char_increase = len(stego_emoji) - len(emoji)
            self.show_popup(
                '✓ Success!',
                f'Message hidden using {mode_name} MODE!\n\n'
                f'• Hidden: {len(hidden_text)} characters\n'
                f'• Size: {len(emoji)} → {len(stego_emoji)} (+{char_increase})\n\n'
                f'Click COPY EMOJI to share!'
            )
        except Exception as e:
            self.show_popup('✕ Error', f'Failed to hide message:\n{str(e)}')
    
    def copy_result(self, instance):
        """Copy result to clipboard."""
        text = self.result_output.text.strip()
        if text:
            Clipboard.copy(text)
            self.show_popup('✓ Copied!', 'Emoji with hidden text copied!\n\nPaste it anywhere to share.')
        else:
            self.show_popup('⚠ Nothing to Copy', 'Please hide a message first!')
    
    def show_popup(self, title, message):
        """Show a popup message."""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, markup=True))
        close_btn = Button(text='OK', size_hint_y=None, height=50)
        content.add_widget(close_btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.9, 0.5))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class DecodeTab(BoxLayout):
    """Decoding tab for revealing hidden text."""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.padding = 15
        self.spacing = 10
        
        # Mode selection
        mode_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=50, spacing=10)
        mode_label = Label(text='[b]Detection Mode:[/b]', markup=True, size_hint_x=0.4)
        self.auto_btn = ToggleButton(text='AUTO', group='decode_mode', state='down', size_hint_x=0.2)
        self.tag_btn = ToggleButton(text='TAG', group='decode_mode', size_hint_x=0.2)
        self.binary_btn = ToggleButton(text='BINARY', group='decode_mode', size_hint_x=0.2)
        mode_layout.add_widget(mode_label)
        mode_layout.add_widget(self.auto_btn)
        mode_layout.add_widget(self.tag_btn)
        mode_layout.add_widget(self.binary_btn)
        self.add_widget(mode_layout)
        
        # Emoji input
        self.add_widget(Label(text='[b]Paste Emoji:[/b]', markup=True, size_hint_y=None, height=30))
        self.stego_input = StyledTextInput(
            hint_text='Paste emoji with hidden text here...',
            size_hint_y=0.2,
            font_size='24sp'
        )
        self.add_widget(self.stego_input)
        
        # Decode button
        decode_btn = Button(
            text='🔓 REVEAL MESSAGE',
            size_hint_y=None,
            height=60,
            background_color=(0.05, 0.45, 0.47, 1),
            font_size='18sp',
            bold=True
        )
        decode_btn.bind(on_press=self.decode_message)
        self.add_widget(decode_btn)
        
        # Result output
        self.add_widget(Label(text='[b]Hidden Message:[/b]', markup=True, size_hint_y=None, height=30))
        self.result_output = StyledTextInput(
            readonly=True,
            size_hint_y=0.4,
            font_size='18sp',
            background_color=(0.15, 0.15, 0.15, 1),
            foreground_color=(1, 0.84, 0, 1)
        )
        self.add_widget(self.result_output)
        
        # Copy button
        copy_btn = Button(
            text='📋 COPY MESSAGE',
            size_hint_y=None,
            height=50,
            background_color=(0, 1, 0.53, 1),
            color=(0.1, 0.1, 0.1, 1),
            font_size='16sp',
            bold=True
        )
        copy_btn.bind(on_press=self.copy_result)
        self.add_widget(copy_btn)
    
    def decode_message(self, instance):
        """Reveal the hidden message from the emoji."""
        stego_emoji = self.stego_input.text.strip()
        
        if not stego_emoji:
            self.show_popup('⚠ Input Required', 'Please paste an emoji!')
            return
        
        try:
            hidden_text = None
            mode_found = ''
            
            if self.auto_btn.state == 'down':
                hidden_text = reveal_text_from_emoji_tags(stego_emoji)
                if hidden_text:
                    mode_found = 'TAG'
                else:
                    hidden_text = decode_text_from_emoji_binary(stego_emoji)
                    if hidden_text:
                        mode_found = 'BINARY'
            elif self.tag_btn.state == 'down':
                hidden_text = reveal_text_from_emoji_tags(stego_emoji)
                mode_found = 'TAG'
            else:
                hidden_text = decode_text_from_emoji_binary(stego_emoji)
                mode_found = 'BINARY'
            
            if hidden_text:
                self.result_output.text = hidden_text
                self.show_popup(
                    '✓ Message Found!',
                    f'Hidden message revealed!\n\n'
                    f'• Mode: {mode_found}\n'
                    f'• Length: {len(hidden_text)} characters'
                )
            else:
                self.result_output.text = 'No hidden message detected.'
                self.show_popup(
                    '⚠ No Message Found',
                    'No hidden message was detected.\n\n'
                    'Try:\n'
                    '• Select a different detection mode\n'
                    '• Make sure you copied the entire emoji'
                )
        except Exception as e:
            self.show_popup('✕ Error', f'Failed to decode:\n{str(e)}')
    
    def copy_result(self, instance):
        """Copy decoded text to clipboard."""
        text = self.result_output.text.strip()
        if text and text != 'No hidden message detected.':
            Clipboard.copy(text)
            self.show_popup('✓ Copied!', 'Message copied to clipboard!')
        else:
            self.show_popup('⚠ Nothing to Copy', 'No message to copy!')
    
    def show_popup(self, title, message):
        """Show a popup message."""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, markup=True))
        close_btn = Button(text='OK', size_hint_y=None, height=50)
        content.add_widget(close_btn)
        
        popup = Popup(title=title, content=content, size_hint=(0.9, 0.5))
        close_btn.bind(on_press=popup.dismiss)
        popup.open()


class EmojiStegoApp(App):
    """Main application class."""
    
    def build(self):
        # Set window title (for desktop testing)
        self.title = '🔐 Emoji Steganography'
        
        # Main layout
        root = BoxLayout(orientation='vertical')
        
        # Title bar
        title = Label(
            text='[b]🔐 EMOJI STEGANOGRAPHY[/b]',
            markup=True,
            size_hint_y=None,
            height=60,
            font_size='24sp',
            color=(0, 1, 0.53, 1)
        )
        root.add_widget(title)
        
        # Tabbed panel
        tab_panel = TabbedPanel(do_default_tab=False, tab_width=150)
        
        # Encode tab
        encode_tab = TabbedPanelItem(text='HIDE')
        encode_tab.add_widget(EncodeTab())
        tab_panel.add_widget(encode_tab)
        
        # Decode tab
        decode_tab = TabbedPanelItem(text='REVEAL')
        decode_tab.add_widget(DecodeTab())
        tab_panel.add_widget(decode_tab)
        
        root.add_widget(tab_panel)
        
        # Instructions
        instructions = Label(
            text='[i]Hide secret messages in emojis!\nUse Gboard for emoji input 😊[/i]',
            markup=True,
            size_hint_y=None,
            height=40,
            font_size='12sp',
            color=(0.6, 0.6, 0.6, 1)
        )
        root.add_widget(instructions)
        
        return root


if __name__ == '__main__':
    # Set background color
    Window.clearcolor = (0.12, 0.12, 0.12, 1)
    EmojiStegoApp().run()
