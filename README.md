# linkedin-job-recommender
Mine/parse LinkedIn jobs and train the model to find the best options for you.

## How to use
1. Clone repository:\
```git clone https://github.com/MaryRa/linkedin-job-recommender.git```
2. Change directory \
```cd linkedin-job-recommender```
3. Create new environment:\
```conda create --name venv python=3.10```
4. Activate new environment:\
```conda activate venv```
5. Install requirements\
```pip install -r requirements.txt```\
6. Change urls, which you want to parse in ```configs/config.yaml```
7. Parse jobs from LinkedIn:\
```python parse_data.py```
8. As soon as you see ```vacancy.csv``` file in local directory, you can run 
the recommender\
```linkedin jobs recommender.ipynb```
![](pics/recommender_view.png)
![](pics/vacany_view.png)


P.S. In order to use created environment, you should choose it in your jupyter 
notebook ![](pics/venv.png)
