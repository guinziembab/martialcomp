import React from 'react';
import { render } from '@testing-library/react-native';
import Translate from '@components/common/Translate';
import i18n from '@i18n/index';

describe('Translate component', () => {
  beforeAll(() => {
    // Set locale to English for consistent tests
    i18n.locale = 'en';
  });

  it('renders translation correctly', () => {
    const { getByText } = render(<Translate text="common.ok" />);
    expect(getByText('OK')).toBeTruthy();
  });

  it('renders translation with params correctly', () => {
    // Mock translation that includes parameters
    i18n.translations.en = {
      ...i18n.translations.en,
      test: {
        params: 'Hello, {{name}}!',
      },
    };

    const { getByText } = render(<Translate text="test.params" params={{ name: 'World' }} />);
    expect(getByText('Hello, World!')).toBeTruthy();
  });

  it('applies style correctly', () => {
    const { getByText } = render(
      <Translate 
        text="common.ok" 
        style={{ fontSize: 20, fontWeight: 'bold' }} 
      />
    );
    
    const textElement = getByText('OK');
    expect(textElement.props.style).toEqual(expect.objectContaining({ 
      fontSize: 20, 
      fontWeight: 'bold',
    }));
  });

  it('passes additional text props correctly', () => {
    const { getByText } = render(
      <Translate 
        text="common.ok" 
        numberOfLines={1}
        ellipsizeMode="tail"
      />
    );
    
    const textElement = getByText('OK');
    expect(textElement.props.numberOfLines).toBe(1);
    expect(textElement.props.ellipsizeMode).toBe('tail');
  });
});