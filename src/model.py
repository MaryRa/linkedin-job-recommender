from sklearn.linear_model import LogisticRegression
from imblearn.over_sampling import RandomOverSampler
from sklearn.metrics import roc_auc_score
from textwrap import wrap


def get_model(df, tf_idf):
    model = LogisticRegression(penalty='l2',
                               solver='liblinear')  # RandomForestClassifier()
    if ('good' in df.columns and
            df['good'].dropna().unique().shape[0] > 1 and
            df['good'].dropna().shape[0] >= 20):

        base_val = df['good'].isna().sum()
        # I want to highlight synthetic class since there we will see the
        # pure 1 or 0 class a bit less highlight vacancies which was scored and
        # the lowest score for vacancies which were not scored yet
        classes = ((df['good'] + 1).fillna(0) + df['synthetic'].fillna(
            0) * 2).astype(int)
        dict_coefs = {
            0: base_val,  # they haven't scored yet
            1: base_val,  # scored as 0 and real job
            2: base_val,  # scored as 1 and real job
            3: base_val * 2,  # scored as 0 and synthetic
            4: base_val * 2  # scored as 1 and synthetic
        }
        dict_coefs = {x: dict_coefs[x] for x in dict_coefs if
                      x in classes.unique()}
        ros = RandomOverSampler(random_state=0, sampling_strategy=dict_coefs)
        train, _ = ros.fit_resample(df, classes)

        train['good'] = train['good'].fillna(0)
        model.fit(tf_idf.transform(train['text']), train['good'].astype(int))

        y_pred_ = model.predict_proba(tf_idf.transform(df['text']))[:, 1]
        metric_message = f'''ROC-AUC (all): {
        roc_auc_score(df["good"].fillna(0), y_pred_):.2f}'''

        true_val = df[~df['good'].isna()]
        if true_val['good'].unique().shape[0] > 1:
            y_pred_true = model.predict_proba(
                tf_idf.transform(true_val["text"]))[:, 1]
            metric_message += f''', (true): {
            roc_auc_score(true_val["good"], y_pred_true):.2f}'''
    else:
        n_char = 120
        metric_message = (
            "------There is not enough data for modelling, you "
            "should review at least 20 vacancies at first  and some of them "
            "should have positive feedback---------- "
            "It's important to use 'good staff' and 'bad stuff' space in the "
            "vacancies to highlight what would be interesting for you and "
            "what would not be. It can help model to select the best option "
            "for you. It can be something copy-pasted from the vacancy "
            "description or write in your own language. It can be also "
            "something not from vacancy description, but you want to add to "
            "train data to improve it's performance. "
            "For example, in vacancy 'R developer' you can put in "
            "'good stuff': Python if it's important for you to see more "
            "options with Python"
        )
        metric_message = "\n".join(wrap(metric_message, n_char))

        vals = min(200, df['text'].shape[0])
        model.fit(tf_idf.transform(df['text'].head(vals)),
                  [0] * (vals - 1) + [1])
    print(metric_message)
    return model
