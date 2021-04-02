import argparse
import os
import re
import shutil


class FullAction(argparse.Action):

    def __init__(self, option_strings, dest, default=None, required=False, help=None, metavar=None):
        super(FullAction, self).__init__(option_strings=option_strings, dest=dest, nargs=0, const=True,
                                         default=default, required=required, help=help)

    def __call__(self, parser, namespace, values, option_string=None):
        if len(namespace.spider) > 0:
            setattr(namespace, self.dest, self.const)
        else:
            parser.error('must used with spider')


class CreateCommand:
    parser = None

    def add_arguments(self):
        parser = argparse.ArgumentParser(description="resolve")
        # subparsers = parser.add_subparsers(help='sub-command help')
        # parser_create = subparsers.add_parser('create', help='add help')

        group = parser.add_mutually_exclusive_group()
        group.add_argument(
            "-s", "--spider", nargs=1, help="创建爬虫 如 hoopa create -s <spider_name>"
        )
        group.add_argument(
            "-p", "--project", nargs=1, help="创建项目 如 hoopa create -p <project_name>"
        )

        parser.add_argument(
            "-f", "--full", help="full spider 如 hoopa create -s <spider_name> -f", default=False, action=FullAction
        )

        self.parser = parser

    def create_spider(self, template_path, spider_name, project=None):
        spider_class_name = spider_name
        if spider_class_name.islower():
            spider_class_name = spider_class_name.title().replace("_", "")

        with open(template_path, "r", encoding="utf-8") as file:
            spider_template = file.read()
        spider_template = spider_template.replace("${spider_name}", spider_name)
        spider_template = spider_template.replace("${spider_class_name}", spider_class_name)
        result = self._save_spider_to_file(spider_template, spider_name, project)

        return result

    @staticmethod
    def copy_callback(src, dst, *, follow_symlinks=True):
        if src.endswith(".py"):
            with open(src, "r", encoding="utf-8") as src_file, open(
                dst, "w", encoding="utf8"
            ) as dst_file:
                content = src_file.read()
                dst_file.write(content)
        else:
            shutil.copy2(src, dst, follow_symlinks=follow_symlinks)

    def create_project(self, template_path, project_name):
        if os.path.exists(project_name):
            print("%s 项目已经存在" % project_name)
            return

        shutil.copytree(template_path, project_name, copy_function=self.copy_callback)

        template_path = self._find_template("project_spider")
        getattr(self, f"create_spider")(template_path, project_name, project_name)

        return True

    def run_cmd(self):
        args = self.parser.parse_args()
        full = args.full

        if args.spider:
            spider_name = args.spider[0]
            create_type = "spider"
        elif args.project:
            spider_name = args.project[0]
            create_type = "project"
        else:
            raise
        # 检查spider_name
        if not re.search("^[a-zA-Z][a-zA-Z0-9_]*$", spider_name):
            raise Exception("命名不规范，请用下划线命名或驼峰命名方式")

        template_path = self._find_template(create_type, full)
        result = getattr(self, f"create_{create_type}")(template_path, spider_name)
        if result:
            print(f"{create_type} {spider_name} create success")

    @staticmethod
    def _find_template(template, full=False):
        if template == "spider":
            if full:
                template_file = "spider_full_template.tmpl"
            else:
                template_file = "spider_template.tmpl"
        else:
            if template == "project_spider":
                template_file = "project_spider_template.tmpl"
            else:
                template_file = "project_template"

        template_path = os.path.abspath(
            os.path.join(__file__, "../../templates", template_file)
        )
        if os.path.exists(template_path):
            return template_path

        print("Unable to find template: %s\n" % template)

    def _save_spider_to_file(self, spider, spider_name, project_name):
        spider_underline = self._cover_to_underline(spider_name)
        if project_name:
            spider_file = f"{project_name}/{spider_underline}.py"
        else:
            spider_file = f"{spider_underline}.py"

        if os.path.exists(spider_file):
            print("文件已存在")
            return

        with open(spider_file, "w", encoding="utf-8") as file:
            file.write(spider)

        return True

    @staticmethod
    def _cover_to_underline(key):
        regex = "[A-Z]*"
        capitals = re.findall(regex, key)

        if capitals:
            for pos, capital in enumerate(capitals):
                if not capital:
                    continue
                if pos == 0:
                    if len(capital) > 1:
                        key = key.replace(capital, capital.lower() + "_", 1)
                    else:
                        key = key.replace(capital, capital.lower(), 1)
                else:
                    if len(capital) > 1:
                        key = key.replace(capital, "_" + capital.lower() + "_", 1)
                    else:
                        key = key.replace(capital, "_" + capital.lower(), 1)

        return key
