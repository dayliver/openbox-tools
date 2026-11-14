"""Minimal Openbox rc.xml fixtures for tests."""

SAMPLE_RC = """<?xml version="1.0"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <resistance>
    <strength>10</strength>
  </resistance>
  <keyboard>
    <chainQuitKey>C-g</chainQuitKey>
    <keybind key="W-Return">
      <action name="Execute">
        <command>alacritty</command>
      </action>
    </keybind>
    <keybind key="W-c">
      <action name="Close"/>
    </keybind>
    <keybind key="W-space">
      <action name="ShowMenu">
        <menu>root-menu</menu>
      </action>
    </keybind>
  </keyboard>
  <mouse>
    <context name="Frame">
      <mousebind button="Left" action="Press">
        <action name="Focus"/>
      </mousebind>
    </context>
  </mouse>
</openbox_config>
"""

STOCK_KEYBOARD = """  <keyboard>
    <chainQuitKey>C-g</chainQuitKey>
    <keybind key="W-Return">
      <action name="Execute">
        <command>alacritty</command>
      </action>
    </keybind>
    <keybind key="W-c">
      <action name="Close"/>
    </keybind>
    <keybind key="W-space">
      <action name="ShowMenu">
        <menu>root-menu</menu>
      </action>
    </keybind>
  </keyboard>
"""

MODIFIED_RC = """<?xml version="1.0"?>
<openbox_config xmlns="http://openbox.org/3.4/rc">
  <resistance>
    <strength>10</strength>
  </resistance>
  <keyboard>
    <chainQuitKey>C-g</chainQuitKey>
    <keybind key="W-Return">
      <action name="Execute">
        <command>kitty</command>
      </action>
    </keybind>
    <keybind key="W-c">
      <action name="Close"/>
    </keybind>
    <keybind key="W-space">
      <action name="ShowMenu">
        <menu>root-menu</menu>
      </action>
    </keybind>
    <keybind key="W-g">
      <action name="Execute">
        <command>geany</command>
      </action>
    </keybind>
  </keyboard>
  <mouse>
    <context name="Frame">
      <mousebind button="Left" action="Press">
        <action name="Focus"/>
      </mousebind>
    </context>
  </mouse>
</openbox_config>
"""
