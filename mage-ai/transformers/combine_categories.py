from pandas import DataFrame

if 'transformer' not in globals():
    from mage_ai.data_preparation.decorators import transformer
if 'test' not in globals():
    from mage_ai.data_preparation.decorators import test


@transformer
def transform(data: DataFrame, *args, **kwargs):

    if not data.empty:
        data['IS_TEXT_HATE_SPEECH'] = data['hate'] | data['hate_threatening']
        data['IS_TEXT_HARASSMENT'] = data['harassment'] | data['harassment_threatening']
        data['IS_TEXT_SELF_HARM'] = data['self_harm'] | data['self_harm_intent'] | data['self_harm_instructions']
        data['IS_TEXT_SEXUAL_CONTENT'] = data['sexual'] | data['sexual_minors']
        data['IS_TEXT_VIOLENCE'] = data['violence'] | data['violence_graphic']

        # Drop the original columns
        data.drop(['hate', 'hate_threatening', 'harassment', 'harassment_threatening',
                'self_harm', 'self_harm_intent', 'self_harm_instructions',
                'sexual', 'sexual_minors', 'violence', 'violence_graphic', 'SUBREDDIT_NAME'], axis=1, inplace=True)

    return data

@test
def test_output(output, *args) -> None:
    """
    Template code for testing the output of the block.
    """
    assert output is not None, 'The output is undefined'
    print(output)