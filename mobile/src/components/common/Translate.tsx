import React from 'react';
import { Text, TextStyle, TextProps } from 'react-native';
import i18n from '@i18n/index';

interface TranslateProps extends TextProps {
  text: string;
  params?: { [key: string]: string | number };
  style?: TextStyle | TextStyle[];
}

/**
 * A component that simplifies translation usage in the UI
 * It wraps the i18n.t() function in a Text component
 * 
 * Usage:
 * <Translate text="auth.login.title" />
 * <Translate text="profile.pendingChanges" params={{ count: 5 }} />
 */
const Translate: React.FC<TranslateProps> = ({ text, params, style, ...props }) => {
  return (
    <Text style={style} {...props}>
      {i18n.t(text, params)}
    </Text>
  );
};

export default Translate;