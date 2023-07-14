import yaml
from src.parser import LinkedInParser

if __name__ == '__main__':
    with open("configs/config.yaml") as f:
        cfg = yaml.load(f, Loader=yaml.FullLoader)
    parser = LinkedInParser(chrome_driver_path=cfg['chrome-driver-path'],
                            vacancy_path=cfg['vacancy-file'],
                            urls=cfg['search-urls'])
    parser.run()
