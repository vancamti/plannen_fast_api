import os
import shutil
import sys


def main(argv=sys.argv):  # pragma NO COVER
    old_storage = "/opt/data/storage/filedir/pairtree/pairtree_root/be/he/er/sp/la/n+"
    for root, _dirs, files in os.walk(old_storage):
        for file in files:
            if file.endswith("_thumb"):
                os.remove(os.path.join(root, file))
            if len(file) < 3:
                os.rename(os.path.join(root, file), os.path.join(root, file.zfill(3)))
    new_storage = "/opt/data/storage/plannen/pairtree_root"
    shutil.rmtree(new_storage)
    shutil.copytree(old_storage, new_storage)
    os.system(
        "find {0} -print | xargs --max-args=1 "
        "--max-procs=100 chown deployer:deploy".format(new_storage)
    )


if __name__ == "__main__":
    main()
