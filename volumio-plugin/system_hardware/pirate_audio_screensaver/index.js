'use strict';

var libQ = require('kew');
var fs = require('fs');
var exec = require('child_process').exec;
var vConf = require('v-conf');

module.exports = PirateAudioScreensaver;

function PirateAudioScreensaver(context) {
  this.context = context;
  this.commandRouter = context.coreCommand;
  this.logger = context.logger;
  this.configManager = context.configManager;
  this.config = new vConf();
}

PirateAudioScreensaver.prototype.onVolumioStart = function () {
  var configFile = this.commandRouter.pluginManager.getConfigurationFile(this.context, 'config.json');
  this.config.loadFile(configFile);
  return libQ.resolve();
};

PirateAudioScreensaver.prototype.onStart = function () {
  var defer = libQ.defer();
  var self = this;

  self.writeEnvironmentFile()
    .then(function () {
      return self.runCommand('sudo systemctl daemon-reload');
    })
    .then(function () {
      return self.runCommand('sudo systemctl enable volumio-screensaver.service');
    })
    .then(function () {
      return self.runCommand('sudo systemctl restart volumio-screensaver.service');
    })
    .then(function () {
      self.logger.info('Pirate Audio Screensaver started');
      defer.resolve();
    })
    .fail(function (error) {
      self.logger.error('Cannot start Pirate Audio Screensaver: ' + error);
      defer.reject(error);
    });

  return defer.promise;
};

PirateAudioScreensaver.prototype.onStop = function () {
  var defer = libQ.defer();
  var self = this;

  self.runCommand('sudo systemctl stop volumio-screensaver.service || true')
    .then(function () {
      return self.runCommand('sudo systemctl disable volumio-screensaver.service || true');
    })
    .then(function () {
      self.logger.info('Pirate Audio Screensaver stopped');
      defer.resolve();
    })
    .fail(function (error) {
      self.logger.error('Cannot stop Pirate Audio Screensaver cleanly: ' + error);
      defer.reject(error);
    });

  return defer.promise;
};

PirateAudioScreensaver.prototype.onRestart = function () {
  var self = this;
  return self.writeEnvironmentFile()
    .then(function () {
      return self.runCommand('sudo systemctl restart volumio-screensaver.service');
    });
};

PirateAudioScreensaver.prototype.getUIConfig = function () {
  var defer = libQ.defer();
  var self = this;
  var langCode = this.commandRouter.sharedVars.get('language_code');

  self.commandRouter.i18nJson(
    __dirname + '/i18n/strings_' + langCode + '.json',
    __dirname + '/i18n/strings_en.json',
    __dirname + '/UIConfig.json'
  )
    .then(function (uiconf) {
      self.setUIValue(uiconf, 'idle_delay_seconds', self.config.get('idle_delay_seconds'));
      self.setUIValue(uiconf, 'font_size', self.config.get('font_size'));
      self.setUIValue(uiconf, 'display_rotation', self.config.get('display_rotation'));
      self.setUIValue(uiconf, 'blank_turns_backlight_off', self.config.get('blank_turns_backlight_off'));
      self.setUIValue(uiconf, 'buttons_enabled', self.config.get('buttons_enabled'));
      self.setUIValue(uiconf, 'button_pins', self.config.get('button_pins'));
      self.setUIValue(uiconf, 'log_level', self.config.get('log_level'));
      defer.resolve(uiconf);
    })
    .fail(function (error) {
      self.logger.error('Cannot load Pirate Audio Screensaver UI config: ' + error);
      defer.reject(error);
    });

  return defer.promise;
};

PirateAudioScreensaver.prototype.saveSettings = function (data) {
  var defer = libQ.defer();
  var self = this;

  self.config.set('idle_delay_seconds', self.getFieldValue(data, 'idle_delay_seconds', 300));
  self.config.set('font_size', self.getFieldValue(data, 'font_size', 58));
  self.config.set('display_rotation', self.getFieldValue(data, 'display_rotation', 90));
  self.config.set('blank_turns_backlight_off', self.getFieldValue(data, 'blank_turns_backlight_off', true));
  self.config.set('buttons_enabled', self.getFieldValue(data, 'buttons_enabled', false));
  self.config.set('button_pins', self.getFieldValue(data, 'button_pins', '5,6,16,24'));
  self.config.set('log_level', self.getFieldValue(data, 'log_level', 'INFO'));

  self.writeEnvironmentFile()
    .then(function () {
      return self.runCommand('sudo systemctl restart volumio-screensaver.service || true');
    })
    .then(function () {
      self.commandRouter.pushToastMessage('success', 'Pirate Audio Screensaver', 'Settings saved');
      defer.resolve();
    })
    .fail(function (error) {
      self.logger.error('Cannot save Pirate Audio Screensaver settings: ' + error);
      self.commandRouter.pushToastMessage('error', 'Pirate Audio Screensaver', 'Cannot save settings');
      defer.reject(error);
    });

  return defer.promise;
};

PirateAudioScreensaver.prototype.writeEnvironmentFile = function () {
  var content = [
    'VOLUMIO_URL=http://127.0.0.1:3000',
    'POLL_SECONDS=2.0',
    'HTTP_TIMEOUT_SECONDS=1.5',
    'IDLE_DELAY_SECONDS=' + this.config.get('idle_delay_seconds'),
    '',
    'BUTTONS_ENABLED=' + this.booleanToEnv(this.config.get('buttons_enabled')),
    'BUTTON_PINS=' + this.config.get('button_pins'),
    'BUTTON_BOUNCE_MS=100',
    '',
    'DISPLAY_WIDTH=240',
    'DISPLAY_HEIGHT=240',
    'DISPLAY_ROTATION=' + this.config.get('display_rotation'),
    'DISPLAY_PORT=0',
    'DISPLAY_CS=1',
    'DISPLAY_DC=9',
    'DISPLAY_BACKLIGHT=13',
    'DISPLAY_SPI_SPEED=80000000',
    'DISPLAY_OFFSET_LEFT=0',
    'DISPLAY_OFFSET_TOP=0',
    '',
    'FONT_SIZE=' + this.config.get('font_size'),
    'FONT_PATH=/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
    'SCREEN_PADDING=8',
    'BLANK_TURNS_BACKLIGHT_OFF=' + this.booleanToEnv(this.config.get('blank_turns_backlight_off')),
    'LOG_LEVEL=' + this.config.get('log_level'),
    ''
  ].join('\n');

  return this.writeRootFile('/etc/volumio-screensaver.env', content);
};

PirateAudioScreensaver.prototype.writeRootFile = function (path, content) {
  var escaped = content.replace(/'/g, "'\\''");
  return this.runCommand("printf '%s' '" + escaped + "' | sudo tee " + path + ' >/dev/null');
};

PirateAudioScreensaver.prototype.runCommand = function (command) {
  var defer = libQ.defer();
  var self = this;

  exec(command, { timeout: 120000 }, function (error, stdout, stderr) {
    if (stdout) {
      self.logger.info(stdout.trim());
    }
    if (stderr) {
      self.logger.warn(stderr.trim());
    }
    if (error) {
      defer.reject(stderr || error.message || error);
    } else {
      defer.resolve(stdout);
    }
  });

  return defer.promise;
};

PirateAudioScreensaver.prototype.getFieldValue = function (data, key, defaultValue) {
  if (!data || typeof data[key] === 'undefined') {
    return defaultValue;
  }
  if (data[key] && typeof data[key].value !== 'undefined') {
    return data[key].value;
  }
  return data[key];
};

PirateAudioScreensaver.prototype.booleanToEnv = function (value) {
  return value === true || value === 'true' ? 'true' : 'false';
};

PirateAudioScreensaver.prototype.setUIValue = function (uiconf, id, value) {
  if (!uiconf || !uiconf.sections) {
    return;
  }

  for (var i = 0; i < uiconf.sections.length; i++) {
    var section = uiconf.sections[i];
    if (!section.content) {
      continue;
    }
    for (var j = 0; j < section.content.length; j++) {
      if (section.content[j].id === id && section.content[j].value) {
        section.content[j].value.value = value;
        return;
      }
    }
  }
};
